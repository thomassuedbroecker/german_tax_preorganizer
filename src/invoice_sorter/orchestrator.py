"""Pipeline orchestration: run every file through the stages and collect results.

A failure in one file never stops the run — errors are attached to that file's
result and it is routed to manual review / the error section.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import ai_review as ai_review_module
from . import audit_log, file_operations, report
from .classifier import classify
from .config import Config
from .extraction_adapter import extract_document
from .metadata_extraction import extract_metadata_hybrid
from .models import DocumentResult, ExtractionStatus, ProcessingStatus
from .routing import route
from .scanner import scan_folder


@dataclass
class RunOptions:
    input_dir: Path
    output_dir: Path
    config: Config
    dry_run: bool = False
    recursive: bool = True
    move: bool = False
    extraction_backend: str = "auto"
    ai_review: bool = False
    ai_model: str = ai_review_module.DEFAULT_OLLAMA_MODEL
    ai_base_url: str = ai_review_module.DEFAULT_OLLAMA_URL


def process_file(source: Path, options: RunOptions) -> DocumentResult:
    """Run the full per-file pipeline. Always returns a result (never raises)."""
    result = DocumentResult(source_path=source)
    config = options.config
    try:
        extraction = extract_document(source, backend=options.extraction_backend)
        class_text = extraction.classify_text()
        # Hold the plain text for routing/length checks; amounts use rich text.
        result.text = class_text
        result.extraction_status = extraction.status
        result.backend = extraction.backend
        if extraction.error:
            result.add_error(extraction.error)

        result.metadata = extract_metadata_hybrid(extraction.text, class_text, config)
        classification = classify(class_text, result.metadata, config)
        result.confidence = classification.confidence
        for note in classification.notes:
            result.add_note(note)

        result.category = route(result, classification, config)
        if result.status != ProcessingStatus.MANUAL_REVIEW:
            # Confidently classified.
            result.status = ProcessingStatus.PENDING

        # Place the file (copy/move/dry-run).
        target = file_operations.place_file(
            source,
            options.output_dir,
            result.category,
            dry_run=options.dry_run,
            move=options.move,
        )
        result.target_path = target
        if options.dry_run:
            if result.status != ProcessingStatus.MANUAL_REVIEW:
                result.status = ProcessingStatus.DRY_RUN
        elif result.status != ProcessingStatus.MANUAL_REVIEW:
            result.status = (
                ProcessingStatus.MOVED if options.move else ProcessingStatus.COPIED
            )
    except Exception as exc:  # defensive: one bad file must not stop the run
        result.status = ProcessingStatus.FAILED
        result.add_error(f"{type(exc).__name__}: {exc}")
        if result.extraction_status == ExtractionStatus.NO_TEXT:
            result.extraction_status = ExtractionStatus.ERROR

    return result


def run(options: RunOptions) -> tuple[list[DocumentResult], report.RunSummary]:
    """Scan, process, and write outputs. Returns results + summary."""
    scan = scan_folder(options.input_dir, recursive=options.recursive)

    if not options.dry_run:
        file_operations.ensure_category_dirs(options.output_dir, options.config, dry_run=False)

    results = [process_file(path, options) for path in scan.supported]

    summary = report.RunSummary(
        total_scanned=len(scan.supported) + len(scan.unsupported),
        unsupported_files=scan.unsupported,
        dry_run=options.dry_run,
        manual_review_category=options.config.manual_review_category,
    )

    if options.ai_review:
        try:
            summary.ai_review = ai_review_module.generate_review(
                results,
                summary,
                ai_review_module.AiReviewOptions(
                    enabled=True,
                    model=options.ai_model,
                    base_url=options.ai_base_url,
                ),
            )
        except Exception as exc:
            summary.ai_review_error = f"{type(exc).__name__}: {exc}"

    # Outputs (report + audit log) are always written, even on dry-run, so the
    # user can preview decisions. They live under the output folder.
    report.write_report(options.output_dir, results, summary)
    audit_log.write_audit_log(
        Path(options.output_dir) / audit_log.AUDIT_LOG_NAME, results
    )

    return results, summary
