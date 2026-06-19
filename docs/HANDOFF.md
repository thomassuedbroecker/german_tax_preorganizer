# Handoff / project status

Snapshot for whoever continues this work (e.g. Codex). Read this first.

## What this is

Local-first CLI + desktop app that scans a folder of PDF/image invoices,
extracts metadata (DE/EN), classifies into configurable categories, copies files
into category folders, and writes a Markdown report + JSONL audit log. Built for
organizing invoices for a tax advisor. **Everything runs on-machine.**

## Current status (2026-06-19)

- ✅ CLI `invoice-sorter` — end-to-end, dry-run + real run.
- ✅ Desktop GUI `invoice-sorter-gui` (PySide6) — threaded, offscreen smoke-tested.
- ✅ Extraction backends: Docling (installed) → light (pdfplumber/pypdf,
  pytesseract) → graceful manual-review. Auto-selected at runtime.
- ✅ **Hybrid extraction (NEW):** `extract_document` now returns two views —
  `text` (rich Docling markdown, used for amounts/metadata) and
  `classification_text` (plain text, used for classification). It prefers the
  light backend's plain text for classification (classifies best) and falls back
  to `normalize_for_classification(text)`. `orchestrator.process_file` classifies
  on `extraction.classify_text()` and extracts metadata with
  `extract_metadata_hybrid(...)`: monetary fields from rich text, missing
  non-monetary fields from plain text.
- ✅ Rule-based classifier + confidence + manual-review routing.
- ✅ Markdown report (11 sections) + JSONL audit log.
- ✅ `scripts/suggest_local_config.py` — builds a git-ignored `categories.local.yaml`.
- ✅ **43 pytest passing** after Codex regression tests for hybrid metadata,
  local-config helper classification, backend selection, and local AI review.
- ✅ Hybrid manual-review verification completed on the 38 local PDFs with output
  outside the repo at `/private/tmp/german_tax_preorganizer_hybrid_out`.
  Final aggregate result: **38 processed, 0 unsupported, 16 manual-review, 22
  classified**. This matches the light-backend manual-review count while keeping
  rich Docling text for monetary metadata.
- ✅ Docling verified on Apple Silicon (torch MPS) and **offline** with
  `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`.

## Live update log

### 2026-06-19 Codex continuation

- Fixed `scripts/suggest_local_config.py` so Docling/hybrid mode classifies on
  `ExtractionResult.classify_text()` while still extracting metadata and vendor
  candidates from rich text.
- Added `extract_metadata_hybrid(...)`: monetary fields stay sourced from rich
  Docling text, while missing non-monetary fields (vendor, invoice date, invoice
  number, payment date, IBAN) fall back to the plain classification text.
- Added `tests/test_suggest_local_config.py` to prevent that helper from
  regressing to rich-text classification.
- Verified `.venv/bin/python -m pytest -q` -> **35 passed**.
- First real-data hybrid dry run completed with 38 processed, 0 unsupported,
  18 manual-review, 20 classified. Light-only count under current code was still
  16 manual-review / 22 classified. The two hybrid regressions were Software /
  Cloud cases that matched the category but fell below confidence threshold
  because a non-monetary field was missing from rich text.
- After broadening the fallback to non-monetary metadata, final real-data hybrid
  dry run completed with **38 processed, 0 unsupported, 16 manual-review, 22
  classified**.
- Implemented backend selection plumbing: `extract_document(path, backend=...)`,
  `RunOptions.extraction_backend`, CLI `--backend`, and GUI Auto/Docling/Light
  combo box.
- Updated README for `--backend`, the GUI selector, and the refined hybrid
  metadata behavior.
- Verified `.venv/bin/python -m pytest -q` -> **38 passed** after backend
  selection changes.
- Added `docs/QUICK_START.md` with first-run setup, dry-run, GUI, local config,
  offline Docling, and test commands. README now links to it near the top.
- Added optional local Ollama AI review integration. It runs after deterministic
  sorting, appends a local AI sorting review to `invoice_summary.md`, and does
  not affect classification or routing. Runtime prompt is code-owned in
  `src/invoice_sorter/ai_review.py`; `prompts/` remains interaction history only.
- Added CLI flags `--ai-review`, `--ai-model`, and `--ai-base-url`; GUI has a
  Local AI review checkbox plus Ollama model/URL fields.
- Verified `.venv/bin/python -m pytest -q` -> **43 passed** after AI review
  changes.
- Starting licensing transparency and GitHub Actions work. Found a license
  mismatch: root `LICENSE` is BSD-2-Clause while `pyproject.toml` declares
  Apache-2.0. The existing BSD-2-Clause license will be treated as authoritative
  and project metadata/docs will be aligned to it.
- Licensing/CI work completed: `pyproject.toml` now uses the SPDX expression
  `BSD-2-Clause` and includes `LICENSE`; added `LICENSE_POLICY.md`,
  `THIRD_PARTY_NOTICES.md`, and `CONTENT_PROVENANCE.md`.
- Added `scripts/check_license_metadata.py`. It verifies project license
  consistency, required transparency files, README links, and direct dependency
  notice coverage.
- Added `.github/workflows/tests.yml` for pushes to `main`, pull requests, and
  manual runs. It uses Python 3.12, read-only contents permission, pip caching,
  license checks, compileall, and pytest.
- Final verification: editable package build/install succeeded; license checker
  passed with 11 direct dependencies/extras covered; workflow YAML parsed;
  compileall passed; pytest -> **43 passed**.
- README test badge is pinned to the `main` branch and the top of README now
  explicitly states that it was developed with AI assistance.

## ⚠️ Privacy rules — do not break

1. `tax_input_docs/` holds **real private invoices**. It is git-ignored. **Never**
   reference its path or contents in code, tests, or committed files. **Never**
   print vendor names / amounts / filenames to the console or chat.
2. Run outputs (`Sorted_Invoices/`, `invoice_summary.md`, `audit_log.jsonl`) and
   `*.local.yaml` are git-ignored. When running on real data, send `--output` to a
   path **outside the repo** (e.g. `/tmp/...`).
3. No network in the processing path. Only extracted metadata is persisted — never
   full invoice text. Copy mode is the default; `--move` is opt-in.

## Key decisions

- **Docling-first** was chosen for extraction quality. BUT see findings below —
  light backend currently classifies better.
- **PySide6** desktop GUI (vs Streamlit/Textual).
- Engine is **UI-agnostic**: `orchestrator.run(RunOptions) -> (results, summary)`.
  `cli.py` and `gui.py` are thin renderers.
- Reuse intent (not yet wired): `docling_preprocessor_factory` (hook exists in
  `extraction_adapter._extract_with_factory`) and `pdf_extraction_macos`
  (PySide6 + Ollama patterns).

## Empirical findings (from the 38 real PDFs)

- All 38 have extractable embedded text — **none needed OCR**.
- Manual-review count: **16** (lean base config) with the light backend.
- **Generic vendor expansion made it worse (16→17)** via category ties — reverted.
  Lesson: keep the committed config lean; put real vendors in `categories.local.yaml`.
- **Docling classified worse (20 manual)** than light, because its Markdown output
  (table cells, `#` headers) disrupts keyword matching. Docling is better for
  amount/VAT extraction. → A hybrid (Docling amounts + plain-text classification)
  is the recommended next architecture step.
- The data-driven `local.yaml` (light backend) got it to **14** automatically;
  most remaining files have no machine-detectable issuer token, so the user must
  assign their own vendors once in the git-ignored file.

## How to run

```bash
# from german_tax_preorganizer/
.venv/bin/python -m pytest -q                      # tests
.venv/bin/invoice-sorter --input ./tax_input_docs --output /tmp/out --dry-run
.venv/bin/invoice-sorter-gui                       # desktop app
.venv/bin/python scripts/suggest_local_config.py --input ./tax_input_docs
```

Environment: `.venv` (Python 3.12.12) has docling 2.104.0, torch 2.12.1,
PySide6, pdfplumber/pypdf, PyYAML, python-dateutil, rich, pytest. Tesseract 5.5.1
installed (eng only; `brew install tesseract-lang` for German OCR via the light
backend).

## Suggested next steps

1. ✅ Done: hybrid verified on the 38 real PDFs. Manual-review count is 16,
   matching the light backend while preserving rich Docling text for monetary
   fields.
2. ✅ Done: GUI backend selector (Auto / Docling / Light) in `gui.py`, backed by
   `RunOptions.extraction_backend`. CLI also has `--backend`.
3. **DOCX export** (`[docx]` extra, `python-docx`) mirroring `report.py`.
4. Partly done: optional local Ollama report review is implemented. Still open:
   optional Ollama assist as a tie-breaker for manual-review files.
5. Help the user finish `categories.local.yaml` for their real vendors.
6. ✅ Done: `scripts/suggest_local_config.py` now uses `classify_text()` for
   classification in both analysis and reroute-count passes.

## Not committed yet

Nothing from this continuation has been committed. Current changed files:

- Modified: `README.md`
- Modified: `docs/HANDOFF.md`
- Modified: `pyproject.toml`
- Untracked: `.github/workflows/tests.yml`
- Untracked: `CONTENT_PROVENANCE.md`
- Untracked: `LICENSE_POLICY.md`
- Untracked: `THIRD_PARTY_NOTICES.md`
- Untracked: `scripts/check_license_metadata.py`

Repo is on `main` with one initial commit. Branch before committing.
