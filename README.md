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

> Note on Docling: if you enable the optional Docling backend, it may download
> layout/OCR **models** from Hugging Face on first use. That is a one-time setup
> download (no invoice data leaves your machine). To guarantee fully offline
> runs afterwards, warm it up once and then set `HF_HUB_OFFLINE=1`.

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
pip install -e ".[docling]" # Docling-first extraction (best tables/amounts; heavy)
pip install -e ".[docx]"    # DOCX export (planned)
pip install -e ".[test]"    # pytest
```

## 4. Required system tools

- **Python 3.12**
- **Tesseract** — only needed to OCR image files / scanned PDFs. The tool runs
  without it; image files are then flagged for manual review instead of crashing.

## 5. Installing Tesseract on macOS

```bash
brew install tesseract
brew install tesseract-lang   # adds German (deu) and other languages
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

- Enable the **Docling** backend by default for better table/amount extraction.
- Image/scanned-PDF **OCR** second pass.
- Optional **DOCX** export for Apple Pages.
- A simple local **GUI** (PySide6) and optional local **Ollama** LLM assist —
  reusing the author's `pdf_extraction_macos` and `docling_preprocessor_factory`
  projects.

## Development

```bash
pip install -e ".[test]"
pytest
```
