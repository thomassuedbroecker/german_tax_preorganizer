"""Optional local AI review of sorting results via Ollama.

This module never participates in classification. It runs after the deterministic
pipeline and sends only aggregate metadata/counts to a local Ollama server. Full
invoice text is never included.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from .models import UNKNOWN, DocumentResult, ProcessingStatus
from .report import RunSummary

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2"


@dataclass
class AiReviewOptions:
    enabled: bool = False
    model: str = DEFAULT_OLLAMA_MODEL
    base_url: str = DEFAULT_OLLAMA_URL
    timeout_seconds: float = 60.0


@dataclass
class AiReviewResult:
    text: str
    metrics: dict[str, Any]


def _fmt(value: Any) -> str:
    if value is None:
        return UNKNOWN
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def _review_payload(results: list[DocumentResult], summary: RunSummary) -> dict[str, Any]:
    manual_cat = summary.manual_review_category
    manual = [
        r for r in results
        if r.status == ProcessingStatus.MANUAL_REVIEW or r.category == manual_cat
    ]
    failed = [r for r in results if r.status == ProcessingStatus.FAILED]
    classified = [r for r in results if r not in manual and r not in failed]
    categories = Counter(r.category for r in results)
    statuses = Counter(r.status.value for r in results)
    manual_reasons = Counter(
        "; ".join(r.notes) if r.notes else "uncertain classification"
        for r in manual
    )
    unknown_fields = Counter()
    for r in results:
        metadata = r.metadata
        fields = {
            "vendor": metadata.vendor,
            "invoice_date": metadata.invoice_date,
            "invoice_number": metadata.invoice_number,
            "gross_amount": metadata.gross_amount,
            "vat_amount": metadata.vat_amount,
            "net_amount": metadata.net_amount,
            "currency": metadata.currency,
        }
        for name, value in fields.items():
            if value is None:
                unknown_fields[name] += 1

    low_confidence = [
        {
            "document_id": f"doc_{index:03d}",
            "category": r.category,
            "confidence": r.confidence,
            "status": r.status.value,
            "notes": list(r.notes),
            "known_metadata": {
                "vendor": _fmt(r.metadata.vendor),
                "invoice_date": _fmt(r.metadata.invoice_date),
                "invoice_number": _fmt(r.metadata.invoice_number),
                "gross_amount": _fmt(r.metadata.gross_amount),
                "currency": _fmt(r.metadata.currency),
            },
        }
        for index, r in enumerate(results, start=1)
        if r.confidence < 0.7 or r in manual or r in failed
    ]

    return {
        "run": {
            "dry_run": summary.dry_run,
            "total_scanned": summary.total_scanned,
            "processed": len(results) - len(failed),
            "classified": len(classified),
            "manual_review": len(manual),
            "failed": len(failed),
            "unsupported": len(summary.unsupported_files),
        },
        "categories": dict(sorted(categories.items())),
        "statuses": dict(sorted(statuses.items())),
        "manual_review_reasons": dict(manual_reasons.most_common(10)),
        "unknown_fields": dict(sorted(unknown_fields.items())),
        "low_confidence_documents": low_confidence[:25],
    }


def build_prompt(results: list[DocumentResult], summary: RunSummary) -> str:
    """Build the runtime prompt for the local AI review.

    This is intentionally code-owned, not read from ``prompts/``. That directory
    documents development interaction history only.
    """
    payload = _review_payload(results, summary)
    return (
        "You are reviewing the output of a local invoice sorting tool for a tax "
        "preparation workflow.\n"
        "Use only the JSON data below. Do not invent vendors, dates, amounts, or "
        "tax advice. Do not ask for file text; full invoice text is unavailable "
        "by design.\n\n"
        "Write a concise Markdown review with these sections:\n"
        "1. Overall result\n"
        "2. Sorting quality\n"
        "3. Manual review priorities\n"
        "4. Configuration improvements\n"
        "5. Cautions for the tax advisor\n\n"
        "Keep it practical and specific to the counts and confidence signals.\n\n"
        f"JSON data:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def generate_review(
    results: list[DocumentResult],
    summary: RunSummary,
    options: AiReviewOptions,
) -> AiReviewResult:
    """Return Markdown review text and inference metrics from local Ollama.

    Raises ``RuntimeError`` with a short message if Ollama is unavailable or
    returns an invalid response. The caller decides whether that is fatal.
    """
    prompt = build_prompt(results, summary)
    url = options.base_url.rstrip("/") + "/api/generate"
    request_body = {
        "model": options.model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=options.timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc
    except TimeoutError as exc:
        raise RuntimeError("Ollama request timed out") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Ollama returned invalid JSON") from exc
    text = str(data.get("response") or "").strip()
    if not text:
        raise RuntimeError("Ollama returned an empty response")

    def seconds(field: str) -> float:
        return round(float(data.get(field) or 0) / 1_000_000_000, 6)

    prompt_tokens = int(data.get("prompt_eval_count") or 0)
    output_tokens = int(data.get("eval_count") or 0)
    metrics = {
        "model": str(data.get("model") or options.model),
        "total_duration_seconds": seconds("total_duration"),
        "load_duration_seconds": seconds("load_duration"),
        "prompt_eval_duration_seconds": seconds("prompt_eval_duration"),
        "inference_duration_seconds": seconds("eval_duration"),
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "total_tokens": prompt_tokens + output_tokens,
    }
    return AiReviewResult(text=text, metrics=metrics)
