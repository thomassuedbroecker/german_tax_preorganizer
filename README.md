# Invoice Sorter

A **local-first** command-line tool that scans a folder of PDF and image
invoices/receipts, extracts metadata, classifies each document into configurable
categories, copies it into a category folder, and produces a Markdown summary for
a tax advisor plus a JSONL audit log.

Built for a private user organizing invoices for a tax advisor. It runs entirely
on your machine.

## 1. What the tool does

1. Recursively scans an input folder for `PDF, JPG, JPEG, PNG, TIFF`.
2. Extracts text (Docling-first, with a lightweight fallback; OCR for images).
3. Extracts invoice metadata: vendor, dates, invoice number, gross/VAT/net,
   currency, IBAN — **German and English** formats.
4. Classifies each file with a transparent rule-based scorer and a confidence
   score.
5. Copies files into `Sorted_Invoices/<Category>/` (copy, never move, by default).
6. Writes `invoice_summary.md` and `audit_log.jsonl`.

## 2. Privacy model

Invoices contain sensitive personal and financial data, so:

- **No network access in the processing path.** Nothing is uploaded.
- **Only extracted metadata is stored** — the full invoice text is never written
  to the report or audit log.
- **Copy mode by default** (originals are never moved or deleted).
- **Dry-run mode** lets you preview every decision before any file is touched.
- **Uncertain results are marked** and routed to a manual-review folder.

> Note on Docling: the optional Docling backend downloads layout/table/OCR
> **models** on first use (Hugging Face + ModelScope for RapidOCR). That is a
> one-time setup download — **no invoice data leaves your machine.** After a
> one-time warm-up the tool runs **fully offline**; enforce it with:
>
> ```bash
> export HF_HUB_OFFLINE=1
> export TRANSFORMERS_OFFLINE=1
> ```
>
> Verified on Apple Silicon (torch MPS): with these set, extraction runs with no
> network access.

## 3. Installation

Requires **Python 3.12**.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .            # core (light deps)
```

Optional backends/extras:

```bash
pip install -e ".[light]"   # pdfplumber/pypdf + pytesseract image OCR (fallback)
pip install -e ".[docling]" # Docling extraction (best tables/amounts; heavy)
pip install -e ".[gui]"     # PySide6 desktop app
pip install -e ".[docx]"    # DOCX export (planned)
pip install -e ".[test]"    # pytest
```

The extraction backend is auto-selected at runtime: **Docling if installed**,
otherwise the **light** backend, otherwise files are flagged for manual review.
Check which is active with:

```bash
python -c "from invoice_sorter.extraction_adapter import active_backend; print(active_backend())"
```

## 4. Required system tools

- **Python 3.12**
- **Tesseract** — only used by the **light** backend to OCR image files /
  scanned PDFs. The **Docling** backend bundles its own OCR (RapidOCR), so
  Tesseract is not needed when Docling is installed. Without either, image files
  are flagged for manual review instead of crashing.

## 5. Installing Tesseract on macOS (light backend only)

```bash
brew install tesseract
brew install tesseract-lang   # adds German (deu); the base install is eng-only
```

## 6. Running the CLI

```bash
invoice-sorter \
  --input "/path/to/input/folder" \
  --output "/path/to/output/folder" \
  --config "config/categories.yaml" \
  --dry-run
```

Options:

| Option | Meaning |
|---|---|
| `--input` | Input folder with PDFs and images (required) |
| `--output` | Output folder for sorted invoices and reports (required) |
| `--config` | Path to category configuration (default: bundled `config/categories.yaml`) |
| `--dry-run` | Analyze only; do not copy files |
| `--recursive` / `--no-recursive` | Scan subfolders (default: on) |
| `--move` | Move instead of copy (default: copy — safer) |
| `--verbose` | Print a per-file line (filenames; avoid when screen-sharing private data) |
| `--version` | Print version and exit |

## 6b. Desktop app (GUI)

A local PySide6 desktop app wraps the same engine:

```bash
pip install -e ".[gui]"
invoice-sorter-gui
```

Pick input/output folders and a config, toggle **Dry run** (on by default),
click **Run**. Results appear in a sortable table (manual-review rows highlighted
amber, failures red, high-confidence green); buttons open the report and output
folder. The work runs in a background thread so the window stays responsive.

## 7. How dry-run works

`--dry-run` runs the **entire** analysis — scan, extract, classify, route — and
writes the report and audit log so you can review decisions, but it **does not
create the `Sorted_Invoices/` tree or copy any file.** Re-run without `--dry-run`
to actually sort.

## 8. Configuring categories

Categories live in [config/categories.yaml](config/categories.yaml). Each
category has `keywords` and optional `vendors`:

```yaml
categories:
  Internet:
    keywords: [Internet, DSL, Glasfaser, Router, Mobilfunk]
    vendors:  [Telekom, Vodafone, 1&1, O2]
```

Folder names are derived automatically (umlauts transliterated, e.g.
`Auto / Mobilität` → `Auto_Mobilitaet`).

**Keep private vendor names out of the repo:** copy the file to a location
outside version control (or a git-ignored `*.local.yaml`) and pass it with
`--config`. The bundled config intentionally contains only generic examples.

### Tuning on your own folder

[scripts/suggest_local_config.py](scripts/suggest_local_config.py) scans a real
folder, finds the files that land in manual review, extracts candidate vendor
tokens, auto-assigns well-known public vendors, and writes a **git-ignored**
`config/categories.local.yaml`. It prints **only counts** — your vendor names go
into the (git-ignored) file, never the console.

```bash
python scripts/suggest_local_config.py --input ./your_folder
#   add --use-docling to extract with Docling instead of the light backend
```

Then open `config/categories.local.yaml`, move the `# REVIEW` vendor tokens
under the right categories, and run with `--config config/categories.local.yaml`.

> **Hybrid extraction (implemented).** Docling's Markdown output (table cells,
> `#` headers) classifies *worse* than plain text, but extracts amounts/VAT
> *better*. So the pipeline now uses **two views**: amounts/metadata come from
> Docling's rich text, while classification runs on a plain-text view (the light
> backend's text when available, else `normalize_for_classification()` of the
> Markdown). You get Docling-quality amounts with light-quality sorting.

## 9. Interpreting the confidence score

| Score | Meaning |
|---|---|
| 0.90 – 1.00 | Very likely correct |
| 0.70 – 0.89 | Probably correct |
| 0.50 – 0.69 | Needs review |
| below 0.50 | Unclear / manual review |

A file is routed to **Unklar / Manuell prüfen** when: text is too short / OCR is
poor, no category keyword matches, several categories tie, no vendor is detected
with low confidence, or confidence is below the configured threshold.

## 10. Known limitations

- Rule-based classification only — accuracy depends on your keyword/vendor lists.
- Vendor detection is config-driven (a configured vendor name must appear in the
  text); unknown vendors show as `Unknown`.
- No line-item extraction, no multi-page invoice merging, no duplicate detection.
- Amounts are extracted, **never computed** — if only the gross is printed, VAT
  and net stay `Unknown`.
- This is an **organizing aid, not tax software.** Verify all figures.

## 11. Future improvements

- **Hybrid extraction:** amounts via Docling, classification via normalized plain
  text (best of both — see the note in §8).
- Optional **DOCX** export for Apple Pages.
- Optional local **Ollama** LLM assist for classification (augmenting, not
  replacing, the rule-based result), following the author's `pdf_extraction_macos`
  project. The `docling_preprocessor_factory` repo can be wired into
  `extraction_adapter._extract_with_factory` if preferred over plain Docling.
- A GUI backend selector (light vs Docling).

Done already: CLI, Docling backend, **PySide6 desktop GUI**, rule-based
classifier, Markdown report, JSONL audit log, dry-run, real-data tuning script.

## Project structure

```
german_tax_preorganizer/
  pyproject.toml                 # py3.12; extras: docling, light, gui, docx, test
  config/
    categories.yaml              # generic, committed
    categories.local.yaml        # git-ignored, your private vendors
  scripts/
    suggest_local_config.py      # build categories.local.yaml from a real folder
  src/invoice_sorter/
    cli.py                       # `invoice-sorter` entry point
    gui.py                       # `invoice-sorter-gui` entry point (PySide6)
    orchestrator.py              # run(): scan -> per-file pipeline -> outputs
    scanner.py                   # recursive file collection
    extraction_adapter.py        # backend selection: factory -> docling -> light
    metadata_extraction.py       # DE/EN amounts, dates, IBAN, invoice no., vendor
    classifier.py                # keyword/vendor scoring + confidence
    routing.py                   # confident category vs. manual review
    file_operations.py           # safe copy, collision-resolving names
    audit_log.py                 # JSONL writer
    report.py                    # Markdown report (RunSummary + build_report)
    config.py / constants.py / models.py
  tests/                         # pytest (30 tests)
  examples/sample_invoice_summary.md
  tax_input_docs/                # git-ignored real invoices (not in repo)
```

The engine is UI-agnostic: both `cli.py` and `gui.py` call
`orchestrator.run(RunOptions)` and render the returned `(results, summary)`.

## Development

```bash
pip install -e ".[test]"
pytest          # 30 tests
```
