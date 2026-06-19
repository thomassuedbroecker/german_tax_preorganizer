"""Tests for optional local AI review generation."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from invoice_sorter.ai_review import AiReviewOptions, build_prompt, generate_review
from invoice_sorter.models import DocumentResult, InvoiceMetadata, ProcessingStatus
from invoice_sorter.report import RunSummary


def _result() -> DocumentResult:
    result = DocumentResult(source_path=Path("/private/input/vendor-secret.pdf"))
    result.category = "Internet"
    result.confidence = 0.42
    result.status = ProcessingStatus.MANUAL_REVIEW
    result.text = "FULL EXTRACTED PRIVATE TEXT MUST NOT LEAK"
    result.metadata = InvoiceMetadata(
        vendor="Telekom",
        invoice_date="2024-03-15",
        invoice_number="INV-1",
        gross_amount=Decimal("50.00"),
        currency="EUR",
    )
    result.add_note("confidence 0.42 below threshold 0.50")
    return result


def test_build_prompt_uses_aggregate_data_not_full_text_or_paths():
    prompt = build_prompt([_result()], RunSummary(total_scanned=1))

    assert "FULL EXTRACTED PRIVATE TEXT" not in prompt
    assert "vendor-secret.pdf" not in prompt
    assert "/private/input" not in prompt
    assert "manual_review" in prompt
    assert "doc_001" in prompt


def test_generate_review_parses_ollama_response(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"response":"## Overall result\\nLooks consistent."}'

    def fake_urlopen(request, timeout):
        assert timeout == 3
        assert request.full_url == "http://127.0.0.1:11434/api/generate"
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    review = generate_review(
        [_result()],
        RunSummary(total_scanned=1),
        AiReviewOptions(enabled=True, timeout_seconds=3),
    )

    assert "Looks consistent." in review
