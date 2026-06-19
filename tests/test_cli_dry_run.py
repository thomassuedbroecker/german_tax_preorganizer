"""End-to-end dry-run test of the orchestrator.

Text extraction is monkeypatched so the test runs without Docling/pdfplumber
installed and is deterministic.
"""

from __future__ import annotations

import json

import pytest

from invoice_sorter import orchestrator
from invoice_sorter.models import ExtractionResult, ExtractionStatus, ProcessingStatus
from invoice_sorter.orchestrator import RunOptions

INTERNET_TEXT = (
    "Rechnung von Telekom fuer DSL Internet Vertrag. "
    "Rechnungsnummer 12345. Rechnungsdatum 01.01.2024. Gesamtbetrag 50,00 EUR."
)


@pytest.fixture
def fake_extract(monkeypatch):
    def _fake(path, backend="auto"):
        return ExtractionResult(
            text=INTERNET_TEXT, unit_count=1, status=ExtractionStatus.OK,
            backend="fake",
        )

    monkeypatch.setattr(orchestrator, "extract_document", _fake)


def test_dry_run_writes_outputs_but_no_copies(tmp_path, config, fake_extract):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "telekom.pdf").write_bytes(b"%PDF-1.4 fake")
    output_dir = tmp_path / "out"

    options = RunOptions(
        input_dir=input_dir, output_dir=output_dir, config=config, dry_run=True
    )
    results, summary = orchestrator.run(options)

    assert len(results) == 1
    assert results[0].category == "Internet"
    assert results[0].status == ProcessingStatus.DRY_RUN

    # Reports were written...
    assert (output_dir / "invoice_summary.md").exists()
    assert (output_dir / "audit_log.jsonl").exists()
    # ...but no file was actually copied (no Sorted_Invoices tree on dry-run).
    assert not (output_dir / "Sorted_Invoices").exists()


def test_real_run_copies_into_category(tmp_path, config, fake_extract):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "telekom.pdf").write_bytes(b"%PDF-1.4 fake")
    output_dir = tmp_path / "out"

    options = RunOptions(
        input_dir=input_dir, output_dir=output_dir, config=config, dry_run=False
    )
    results, summary = orchestrator.run(options)

    assert results[0].status == ProcessingStatus.COPIED
    copied = output_dir / "Sorted_Invoices" / "Internet" / "telekom.pdf"
    assert copied.exists()

    # Audit log is valid JSONL with one entry.
    lines = (output_dir / "audit_log.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["category"] == "Internet"
    assert entry["status"] == "copied"


def test_run_options_pass_extraction_backend(tmp_path, config, monkeypatch):
    seen = []

    def _fake(path, backend="auto"):
        seen.append(backend)
        return ExtractionResult(
            text=INTERNET_TEXT,
            unit_count=1,
            status=ExtractionStatus.OK,
            backend="fake",
        )

    monkeypatch.setattr(orchestrator, "extract_document", _fake)
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "telekom.pdf").write_bytes(b"%PDF-1.4 fake")

    options = RunOptions(
        input_dir=input_dir,
        output_dir=tmp_path / "out",
        config=config,
        dry_run=True,
        extraction_backend="light",
    )

    orchestrator.run(options)

    assert seen == ["light"]


def test_ai_review_failure_is_nonfatal(tmp_path, config, fake_extract, monkeypatch):
    def fail_review(*_args, **_kwargs):
        raise RuntimeError("Ollama unavailable")

    monkeypatch.setattr(orchestrator.ai_review_module, "generate_review", fail_review)
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "telekom.pdf").write_bytes(b"%PDF-1.4 fake")

    options = RunOptions(
        input_dir=input_dir,
        output_dir=tmp_path / "out",
        config=config,
        dry_run=True,
        ai_review=True,
    )

    results, summary = orchestrator.run(options)

    assert len(results) == 1
    assert "Ollama unavailable" in summary.ai_review_error
    report = (tmp_path / "out" / "invoice_summary.md").read_text()
    assert "AI review unavailable" in report
