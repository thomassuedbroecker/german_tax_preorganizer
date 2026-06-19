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
- ✅ Rule-based classifier + confidence + manual-review routing.
- ✅ Markdown report (11 sections) + JSONL audit log.
- ✅ `scripts/suggest_local_config.py` — builds a git-ignored `categories.local.yaml`.
- ✅ **30 pytest passing.**
- ✅ Docling verified on Apple Silicon (torch MPS) and **offline** with
  `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`.

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

1. **Hybrid extraction**: in `extraction_adapter`, return both a Docling-parsed
   amount view and a normalized plain-text view; classify on the text, take
   amounts from Docling. Removes the light-vs-Docling tradeoff.
2. **GUI backend selector** (light vs Docling) in `gui.py`.
3. **DOCX export** (`[docx]` extra, `python-docx`) mirroring `report.py`.
4. **Ollama assist** (optional, local) as a tie-breaker for manual-review files.
5. Help the user finish `categories.local.yaml` for their real vendors.

## Not committed yet

Nothing has been committed. Repo is on `main` with one initial commit; all new
files are untracked. Branch before committing.
