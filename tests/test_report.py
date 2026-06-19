"""Tests for Markdown report generation."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from invoice_sorter.models import (
    DocumentResult,
    InvoiceMetadata,
    ProcessingStatus,
)
from invoice_sorter.report import RunSummary, build_report


def _sample_results():
    ok = DocumentResult(source_path=Path("telekom.pdf"))
    ok.category = "Internet"
    ok.confidence = 0.82
    ok.status = ProcessingStatus.COPIED
    ok.metadata = InvoiceMetadata(
        vendor="Telekom", invoice_date="2024-03-15", invoice_number="12345",
        gross_amount=Decimal("50.00"), currency="EUR",
    )

    unclear = DocumentResult(source_path=Path("scan.png"))
    unclear.category = "Unklar / Manuell prüfen"
    unclear.status = ProcessingStatus.MANUAL_REVIEW
    unclear.add_note("little or no readable text")

    failed = DocumentResult(source_path=Path("broken.pdf"))
    failed.status = ProcessingStatus.FAILED
    failed.add_error("corrupt PDF")
    return [ok, unclear, failed]


def test_report_contains_all_sections():
    results = _sample_results()
    summary = RunSummary(total_scanned=3, dry_run=False)
    md = build_report(results, summary)

    assert "# Invoice Summary" in md
    assert "## 1. Executive summary" in md
    assert "## 2. Category summary" in md
    assert "## 3. Full invoice table" in md
    assert "Files requiring manual review" in md
    assert "## 5. Errors" in md
    assert "Notes for the tax advisor" in md

    # Data shows up.
    assert "telekom.pdf" in md
    assert "Telekom" in md
    assert "scan.png" in md
    assert "corrupt PDF" in md
    # Missing values rendered as Unknown, never invented.
    assert "Unknown" in md


def test_dry_run_banner():
    summary = RunSummary(total_scanned=0, dry_run=True)
    md = build_report([], summary)
    assert "DRY RUN" in md


def test_write_report(tmp_path):
    from invoice_sorter.report import write_report

    summary = RunSummary(total_scanned=3)
    path = write_report(tmp_path, _sample_results(), summary)
    assert path.exists()
    assert path.name == "invoice_summary.md"
