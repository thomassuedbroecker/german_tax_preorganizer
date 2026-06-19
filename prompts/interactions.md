initial_prompt.md#1-670
Verstanden. Dann würde ich den Prompt klar auf **Python-only** ausrichten und nicht mehr SwiftUI vergleichen lassen.

Hier ist die angepasste Version:

````text
You are an expert Python application engineer and AI-assisted software architect.

Build a local-first Python application for macOS that scans a selected folder containing PDF files and image files, detects what kind of invoices or receipts they are, classifies them into categories, copies the files into category folders, and creates a structured invoice summary for tax preparation.

The application is intended for a private user who wants to organize invoices for a tax advisor.

## Core requirement

Implement the application in Python.

Do not use SwiftUI.
Do not create a native macOS app in the first version.
Start with a working Python prototype.

The first version should provide:

1. A command-line interface.
2. A simple local GUI only if the CLI works reliably.
3. Local file processing.
4. Markdown report generation.
5. Optional DOCX export later, so the result can be opened in Apple Pages.

## Important privacy requirement

Invoices contain sensitive personal and financial data.

Therefore:

- Do not upload files to external services.
- Do not use cloud APIs by default.
- Do not log full invoice text by default.
- Store only extracted metadata.
- Use copy mode by default, not move mode.
- Provide a dry-run mode.
- Keep an audit log.
- Mark uncertain results clearly.

## Supported input files

Scan a selected folder recursively for:

- PDF
- JPG
- JPEG
- PNG
- TIFF

Ignore unsupported files, but list them in the final report.

## Main categories

Use these initial categories:

- Haushalt
- Internet
- Arbeit
- Musik
- Auto / Mobilität
- Versicherung
- Gesundheit
- Software / Cloud Services
- Bank / Finanzen
- Steuern
- Unklar / Manuell prüfen
- Sonstiges

Categories must be configurable through a YAML or JSON configuration file.

## Required output folder structure

Create an output folder named:

```text
Sorted_Invoices/
````

Inside it, create folders like:

```text
Sorted_Invoices/
  Haushalt/
  Internet/
  Arbeit/
  Musik/
  Auto_Mobilitaet/
  Versicherung/
  Gesundheit/
  Software_Cloud_Services/
  Bank_Finanzen/
  Steuern/
  Unklar_Manuell_pruefen/
  Sonstiges/
```

Use safe folder names without special characters where necessary.

## Required reports

Generate these files:

```text
invoice_summary.md
audit_log.jsonl
```

Optional later:

```text
invoice_summary.docx
```

The DOCX export should be implemented only after the Markdown export works.

## Markdown report structure

The Markdown report must include:

1. Executive summary
2. Total scanned files
3. Total processed files
4. Number of recognized invoices
5. Number of unclear documents
6. Number of failed files
7. Category summary
8. Full invoice table
9. Manual review section
10. Error section
11. Notes for the tax advisor

## Invoice table

The report table should contain:

| File Name | Category | Vendor | Invoice Date | Invoice Number | Gross Amount | VAT | Net Amount | Currency | Confidence | Notes |

Rules:

* Do not invent values.
* If a value cannot be extracted, write `Unknown`.
* If confidence is low, put the file into `Unklar / Manuell prüfen`.
* Keep the original file name unless explicit renaming is enabled later.

## Processing pipeline

Implement this pipeline:

1. Parse command-line arguments.
2. Validate input folder.
3. Create output folder.
4. Recursively collect supported files.
5. Extract text from PDFs and images.
6. Normalize extracted text.
7. Extract invoice metadata.
8. Classify document using configurable rules.
9. Calculate confidence score.
10. Copy file into the target category folder.
11. Write audit log entry.
12. Generate Markdown report.
13. Print final summary to console.

## CLI requirements

Create a CLI like this:

```bash
python invoice_sorter.py \
  --input "/path/to/input/folder" \
  --output "/path/to/output/folder" \
  --config "config/categories.yaml" \
  --dry-run
```

Supported options:

```text
--input        Input folder with PDFs and images
--output       Output folder for sorted invoices and reports
--config       Path to category configuration
--dry-run      Analyze only, do not copy files
--copy         Copy files instead of moving them, default true
--recursive    Scan subfolders, default true
--verbose      Print more details
```

Default behavior:

* Recursive scan enabled.
* Copy mode enabled.
* No file deletion.
* No cloud processing.
* Dry-run available.

## Text extraction

Use a layered extraction strategy:

### PDFs

First try direct text extraction from PDF.

Recommended libraries:

* `pypdf`
* or `pdfplumber`

If no useful text is found, mark the file as OCR-needed.

OCR for scanned PDFs can be added as a second step.

### Images

Use OCR for image files.

Recommended OCR options:

* `pytesseract`
* `ocrmypdf` for scanned PDFs if available
* `Pillow` for image handling

The implementation must not crash if OCR tools are missing.

If OCR is not installed, explain this clearly in the README and mark image files as requiring manual review.

## Metadata extraction

Try to extract:

* Vendor
* Invoice date
* Invoice number
* Gross amount
* VAT amount
* Net amount
* Currency
* Payment date, if available
* IBAN, if available
* Category
* Confidence score

Use conservative extraction.

Never invent missing data.

If uncertain, use:

```text
Unknown
```

## German invoice support

The app should support German invoice formats.

Search for terms like:

```text
Rechnung
Rechnungsnummer
Rechnungs-Nr.
Belegnummer
Datum
Rechnungsdatum
Gesamtbetrag
Bruttobetrag
Nettobetrag
MwSt
Umsatzsteuer
UST
EUR
IBAN
Zahlungsdatum
```

Also support English invoice terms:

```text
Invoice
Invoice Number
Invoice Date
Total
Subtotal
VAT
Tax
Amount Due
Payment Date
```

## Classification logic

Start with transparent rule-based classification.

Do not use an LLM in the first version.

The classifier should use:

* Category keywords
* Vendor keywords
* Metadata completeness
* OCR quality
* Conflict detection
* Confidence scoring

## Example category rules

Create a configuration file:

```yaml
categories:
  Haushalt:
    keywords:
      - Strom
      - Gas
      - Wasser
      - Nebenkosten
      - Haushalt
      - Möbel
      - Baumarkt
      - Reparatur
      - Wartung

  Internet:
    keywords:
      - Telekom
      - Vodafone
      - 1&1
      - Internet
      - DSL
      - Glasfaser
      - Router
      - Mobilfunk

  Arbeit:
    keywords:
      - Business
      - Weiterbildung
      - Konferenz
      - Workshop
      - Fachbuch
      - Büro
      - Arbeitsmittel
      - Notebook
      - Monitor

  Musik:
    keywords:
      - Drums
      - Schlagzeug
      - Musik
      - Instrument
      - Mikrofon
      - Audio Interface
      - Logic Pro
      - Plugin
      - Band
      - Studio
      - PA
      - Becken
      - Snare

  Software_Cloud_Services:
    keywords:
      - OpenAI
      - Anthropic
      - GitHub
      - Microsoft
      - Apple
      - Google
      - IBM Cloud
      - Cloud
      - Subscription
      - SaaS
      - API
      - License
```

## Confidence scoring

Use a score from `0.0` to `1.0`.

Example interpretation:

```text
0.90 - 1.00: Very likely correct
0.70 - 0.89: Probably correct
0.50 - 0.69: Needs review
below 0.50: Unclear / manual review
```

Put files into `Unklar / Manuell prüfen` when:

* OCR quality is poor
* no useful text is extracted
* no vendor is detected
* no invoice-like terms are found
* several categories match equally
* confidence is below 0.50

## File handling

Do not overwrite files.

If a target filename already exists, create a unique name:

```text
originalname_001.pdf
originalname_002.pdf
originalname_003.pdf
```

Do not rename files automatically in the first version.

Optional future feature:

```text
YYYY-MM-DD_VENDOR_CATEGORY_AMOUNT.pdf
```

But keep this disabled for now.

## Audit log

Create an audit log file:

```text
audit_log.jsonl
```

Each line should contain one JSON object:

```json
{
  "source_file": "...",
  "target_file": "...",
  "category": "...",
  "confidence": 0.82,
  "vendor": "...",
  "invoice_date": "...",
  "gross_amount": "...",
  "vat": "...",
  "net_amount": "...",
  "currency": "EUR",
  "status": "copied",
  "notes": "..."
}
```

## Error handling

The program must handle:

* Password-protected PDFs
* Corrupt PDFs
* Empty OCR result
* Unsupported file types
* Missing permissions
* Duplicate filenames
* Large folders
* OCR tool not installed
* Files with no readable text

The application must not stop because one file fails.

Failed files should appear in the Markdown report under:

```text
Files requiring manual review
```

## Project structure

Create a maintainable Python project structure:

```text
invoice-sorter/
  README.md
  pyproject.toml
  src/
    invoice_sorter/
      __init__.py
      cli.py
      scanner.py
      text_extraction.py
      metadata_extraction.py
      classifier.py
      file_operations.py
      report.py
      audit_log.py
      config.py
      models.py
  config/
    categories.yaml
  tests/
    test_classifier.py
    test_metadata_extraction.py
    test_file_operations.py
    test_report.py
  examples/
    sample_invoice_summary.md
```

## Recommended Python libraries

Use:

```text
pypdf or pdfplumber
pytesseract
Pillow
PyYAML
python-dateutil
rich
pytest
```

Optional later:

```text
python-docx
ocrmypdf
textual
streamlit
```

Do not add unnecessary dependencies.

## README requirements

The README must explain:

1. What the tool does
2. Privacy model
3. Installation
4. Required system tools
5. How to install Tesseract on macOS
6. How to run the CLI
7. How dry-run works
8. How categories can be configured
9. How to interpret the confidence score
10. Known limitations
11. Future improvements

For macOS, include:

```bash
brew install tesseract
brew install tesseract-lang
```

and Python setup instructions.

## Tests

Create tests for:

* category classification
* ambiguous classification
* unknown document
* German invoice terms
* English invoice terms
* amount extraction
* date extraction
* duplicate filename handling
* Markdown report generation
* dry-run behavior

## Implementation order

Do not generate the complete application blindly.

Work in this order:

1. Create project structure.
2. Implement data models.
3. Implement folder scanner.
4. Implement PDF text extraction.
5. Implement image OCR extraction with graceful fallback.
6. Implement metadata extraction.
7. Implement rule-based classifier.
8. Implement file copy logic.
9. Implement audit log.
10. Implement Markdown report.
11. Implement CLI.
12. Add tests.
13. Add README.
14. Run tests.
15. Fix errors.

## Definition of Done

The prototype is complete when:

* The CLI can scan a folder.
* PDFs with embedded text can be processed.
* Images can be OCR-processed if Tesseract is installed.
* Documents are classified into configured categories.
* Files are copied into category folders.
* Unclear files go into `Unklar_Manuell_pruefen`.
* `invoice_summary.md` is generated.
* `audit_log.jsonl` is generated.
* Dry-run mode works.
* Tests exist and pass.
* README explains installation and usage.
* No files are uploaded to external services by default.

## Important coding rules

* Use type hints.
* Use dataclasses or Pydantic-style models, but avoid heavy dependencies unless justified.
* Keep functions small.
* Keep modules focused.
* Avoid global state.
* Never invent invoice data.
* Be conservative with classification.
* Prefer manual review over false confidence.
* Use simple English in documentation.

````

## Kürzerer Start-Prompt

Falls Claude/Codex zuerst nur planen soll:

```text
Analyze the following requirement and create a Python-only architecture for a local-first macOS invoice sorter.

The app should scan a folder with PDFs and images, extract invoice text, detect invoice metadata, classify invoices into categories such as Haushalt, Internet, Arbeit, Musik, Software, Versicherungen, etc., copy the files into category folders, and generate a Markdown summary for a tax advisor.

Important constraints:
- Python only
- local-first
- no cloud upload by default
- CLI first
- GUI later
- Markdown report first
- optional DOCX export later for Apple Pages
- rule-based classification first
- optional local LLM later

Do not write code yet.
First propose:
1. architecture
2. project structure
3. libraries
4. processing pipeline
5. risks and limitations
6. implementation steps
````

## Meine konkrete Empfehlung

Für deine App wäre diese Reihenfolge am stabilsten:

| Phase | Ziel                                           |
| ----- | ---------------------------------------------- |
| 1     | CLI-Prototyp mit PDF-Textauszug                |
| 2     | Bild-OCR mit Tesseract                         |
| 3     | Regelbasierte Kategorisierung                  |
| 4     | Markdown-Report für Steuerberater              |
| 5     | Audit-Log                                      |
| 6     | einfache GUI, z. B. Streamlit oder Textual     |
| 7     | optional `.docx` für Pages                     |
| 8     | optional lokale LLM-Klassifikation über Ollama |

Ich würde **nicht mit einer GUI starten**. Erst muss die Erkennung und Sortierung zuverlässig funktionieren. Danach kann man eine Oberfläche darüber setzen.
Bash List workspace and project directory contents
IN
ls -la && echo "---GERMAN TAX---" && ls -la german_tax_preorganizer 2>/dev/null && echo "---PROMPTS---" && ls -la german_tax_preorganizer/prompts 2>/dev/null

OUT
total 0
drwxr-xr-x   3 thomassuedbroecker  staff   96 Jun 19 21:08 .
drwxr-xr-x@ 12 thomassuedbroecker  staff  384 Jun 19 21:07 ..
drwxr-xr-x@  6 thomassuedbroecker  staff  192 Jun 19 21:10 german_tax_preorganizer
---GERMAN TAX---
total 24
drwxr-xr-x@  6 thomassuedbroecker  staff   192 Jun 19 21:10 .
drwxr-xr-x   3 thomassuedbroecker  staff    96 Jun 19 21:08 ..
drwxr-xr-x@ 13 thomassuedbroecker  staff   416 Jun 19 21:08 .git
-rw-r--r--@  1 thomassuedbroecker  staff  4628 Jun 19 21:08 .gitignore
-rw-r--r--@  1 thomassuedbroecker  staff  1308 Jun 19 21:08 LICENSE
drwxr-xr-x@  3 thomassuedbroecker  staff    96 Jun 19 21:10 prompts
---PROMPTS---
total 0
drwxr-xr-x@ 3 thomassuedbroecker  staff   96 Jun 19 21:10 .
drwxr-xr-x@ 6 thomassuedbroecker  staff  192 Jun 19 21:10 ..
-rw-r--r--@ 1 thomassuedbroecker  staff    0 Jun 19 21:10 initial_prompt.md
I see the setup: german_tax_preorganizer/ is a git repo with a .gitignore, LICENSE, and an empty prompts/initial_prompt.md (0 bytes — the content only exists in your editor selection, not saved to disk yet).

You've shared a detailed build spec for a local-first German invoice sorter (Python, CLI-first, OCR, rule-based classification, Markdown report for a tax advisor), but you haven't told me what you'd like me to do with it. Let me confirm before I act.

AskUserQuestion
OUT
Your questions have been answered: "What should I do with this invoice-sorter spec?"="Plan first, no code". You can now continue with these answers in mind.
Planning only — no code. Here's the architecture proposal for the local-first invoice sorter.

1. Architecture
Style: A single-process, layered pipeline (a "pipes and filters" architecture). Each stage is a pure-ish function that takes a document record and enriches it. This keeps the system testable, debuggable, and easy to extend later (GUI, DOCX, local LLM) without touching the core.


┌─────────────────────────────────────────────────────────────┐
│ CLI layer (argparse) — parse args, validate, orchestrate      │
└───────────────┬─────────────────────────────────────────────┘
                │ Config (categories.yaml) loaded once
┌───────────────▼─────────────────────────────────────────────┐
│ Orchestrator — runs the pipeline per file, collects results   │
└───────────────┬─────────────────────────────────────────────┘
   ┌────────────┼─────────────────────────────────────────┐
   ▼            ▼            ▼           ▼          ▼        ▼
Scanner → TextExtraction → Metadata → Classifier → FileOps → Audit
(walk)    (PDF text/OCR)   (regex)    (rules+conf) (copy)    (jsonl)
                                                              │
                                              ┌───────────────▼─────┐
                                              │ Report (Markdown)    │
                                              └──────────────────────┘
Key design decisions:

Immutable result object per file. Each file becomes one DocumentResult that accumulates state (raw_text, metadata, category, confidence, status, notes, errors). Stages never mutate global state — they return enriched copies or set fields on the per-file object. This satisfies the "avoid global state" rule and makes every stage unit-testable in isolation.
Errors are data, not exceptions that halt. Every stage wraps its work; a failure attaches an error to the DocumentResult and the file flows to "manual review." The orchestrator never lets one bad file stop the run.
Capability detection, not hard dependencies. OCR (Tesseract/pytesseract) is detected at startup. If missing, image files and scanned PDFs are flagged OCR_REQUIRED rather than crashing. The report and console state this clearly.
Privacy by construction. No network code anywhere in the dependency graph. Raw text lives only in memory during a file's processing and is discarded after metadata extraction — only metadata is persisted. The audit log and report store extracted fields, never full invoice text (unless a future explicit --debug-dump-text flag is added).
Two-pass for safety. Pass 1 = analyze all files and build results (this is exactly what --dry-run stops at). Pass 2 = copy files + write outputs. Dry-run is therefore "everything except side effects," which makes it a genuine preview.
Confidence drives routing, classification suggests. The classifier produces a best-guess category and a confidence; a separate routing rule decides whether the file actually goes to that category or to Unklar_Manuell_pruefen (threshold < 0.50, ties, no vendor, no invoice terms, poor OCR). Keeping routing separate from classification makes the "prefer manual review over false confidence" rule explicit and tunable.
2. Project structure
This follows the spec's src/ layout, with a couple of additions for testability:


invoice-sorter/
  README.md
  pyproject.toml
  src/invoice_sorter/
    __init__.py
    cli.py                 # argparse, wires everything, prints summary
    orchestrator.py        # runs pipeline over all files (NEW vs spec)
    scanner.py             # recursive collection, extension filtering
    text_extraction.py     # PDF text → OCR fallback dispatch
    metadata_extraction.py # regex-based field extraction (DE + EN)
    classifier.py          # keyword scoring + confidence
    routing.py             # decide final folder vs. manual review (NEW)
    file_operations.py     # safe copy, unique-name collision handling
    audit_log.py           # jsonl writer
    report.py              # Markdown generation
    config.py              # load + validate categories.yaml
    capabilities.py        # detect tesseract/optional libs (NEW)
    models.py              # dataclasses: DocumentResult, Metadata, etc.
    constants.py           # category→safe-folder map, term lists (NEW)
  config/
    categories.yaml
  tests/
    test_scanner.py
    test_text_extraction.py
    test_metadata_extraction.py
    test_classifier.py
    test_routing.py
    test_file_operations.py
    test_report.py
    test_cli_dry_run.py
    fixtures/              # tiny sample PDFs + text snippets
  examples/
    sample_invoice_summary.md
The three additions (orchestrator, routing, capabilities, constants) keep cli.py thin and isolate the trickiest logic for testing. I'd keep them; they don't add dependencies.

3. Libraries
Concern	Choice	Why
PDF text	pdfplumber	Better layout/word extraction than pypdf for amounts in tables; handles most embedded-text PDFs. (pypdf as lightweight fallback.)
Image OCR	pytesseract + Pillow	Standard local OCR; Tesseract installed via Homebrew. Optional.
Scanned PDF OCR	ocrmypdf (optional, later)	Phase 2 — adds an OCR text layer to image-only PDFs.
Config	PyYAML	Spec requirement; YAML is friendlier for the keyword lists.
Dates	python-dateutil	Robust German/English date parsing.
CLI output	rich	Readable console summary + progress.
Tests	pytest	Spec requirement.
Deliberately deferred: python-docx (Phase 7), streamlit/textual (Phase 6 GUI), Ollama/local LLM (Phase 8). No pydantic — dataclasses cover the models without a heavy dependency, matching the coding rules.

Standard library only for: argparse, pathlib, re, json, shutil, logging, dataclasses.

4. Processing pipeline
Maps 1:1 to the spec's 13 steps, with the dry-run cut line made explicit:


STARTUP
  1. Parse CLI args
  2. Validate input folder (exists, readable)
  3. Load + validate config (categories.yaml)
  4. Detect capabilities (tesseract present? ocrmypdf?)

ANALYZE (per file — this is the whole of --dry-run)
  5. Scan: collect supported files recursively; record unsupported
  6. Extract text:
       PDF → pdfplumber; if text < threshold → mark OCR_NEEDED
       image → pytesseract if available, else OCR_REQUIRED
  7. Normalize text (whitespace, umlaut/encoding cleanup, lowercase copy for matching)
  8. Extract metadata (vendor, dates, invoice no., gross/VAT/net, currency, IBAN)
  9. Classify: score categories by keyword/vendor hits
 10. Score confidence (term presence + metadata completeness + OCR quality − conflicts)
 11. Route: choose target category OR Unklar_Manuell_pruefen
        ── dry-run STOPS here; results held in memory ──

COMMIT (skipped entirely on dry-run)
 12. Create output tree (Sorted_Invoices/<safe category folders>)
 13. Copy file → target folder, resolving name collisions (_001, _002…)
 14. Append audit_log.jsonl entry

FINALIZE
 15. Generate invoice_summary.md
 16. Print console summary (rich table)
Confidence model (transparent, no ML): start at 0, add weighted points for: invoice-like terms present, a parsed amount, a parsed date, an invoice number, a matched vendor, a clear single-category keyword winner. Subtract for: empty/short OCR text, multiple categories tied within a margin. Normalize to 0.0–1.0. Every contributing factor is recorded in notes so a human can see why — this is what makes the tax-advisor report trustworthy.

5. Risks and limitations
Extraction accuracy (highest risk):

German amount formatting (1.234,56 €) vs English (1,234.56) — decimal/thousand separators are inverted. Needs locale-aware parsing or it will silently misread amounts. Mitigation: dedicated amount parser with German-first heuristics; never guess — emit Unknown on ambiguity.
Net/VAT/Gross relationships: a document may show only gross. Don't compute the others unless the math checks out (gross = net + vat); otherwise leave Unknown. Aligns with "never invent data."
Vendor detection has no reliable anchor in free text. Likely the weakest field; vendor keywords from config will catch known suppliers, unknowns become Unknown → lowers confidence → manual review. That's the correct conservative behavior.
OCR:

Quality varies wildly with scan resolution; Tesseract on a poor scan produces garbage that looks like text. Need an OCR-quality heuristic (character/word ratios, dictionary-hit rate) to avoid false confidence.
Tesseract + German language pack must be installed separately (brew install tesseract tesseract-lang). If absent, image-heavy folders yield mostly manual-review items — must be loud about this.
Classification:

Keyword overlap (e.g. "Apple" could be Software or a hardware purchase under Arbeit) causes ties. Routing-to-manual-review handles it, but heavy overlap means lots of manual items until keywords are tuned. This is expected for a v1 rule-based system and is honest, not a defect.
Edge cases the design must cover explicitly: password-protected PDFs (catch, flag), corrupt PDFs, zero-byte/huge files, duplicate filenames across subfolders, permission errors, non-UTF8 filenames.

Scope limits for v1 (state in README): no multi-page invoice merging, no line-item extraction, no learning from corrections, no de-duplication of the same invoice appearing twice, classification is keyword-only.

Legal/usage note: this is an organizing aid for a tax advisor, not tax software — the report should say so, and every amount carries a confidence flag.

6. Implementation steps
Phased to match your stability table, with the spec's 15-step order folded in. Each phase is independently runnable and testable.

Skeleton + models + config — project layout, pyproject.toml, models.py dataclasses, config.py loader with validation, categories.yaml, constants.py (category→safe-folder map). Test: config load/validate.
Scanner — recursive walk, extension filter, unsupported-file collection. Test: scanner on a fixture tree.
PDF text extraction — pdfplumber path + OCR-needed detection. Test: embedded-text fixture PDF.
Image/scanned-PDF OCR with graceful fallback — capability detection, pytesseract path, clean degradation when absent. Test: capability flag forces manual-review path.
Metadata extraction — DE+EN term lists, locale-aware amount parser, dateutil dates, IBAN/invoice-number regex. Test: German + English snippets, amount/date parsing, Unknown on ambiguity.
Classifier + confidence + routing — keyword scoring, confidence model, manual-review routing. Test: clear case, ambiguous tie, unknown doc, sub-threshold.
File operations — safe copy, collision-resolving unique names, never overwrite/delete. Test: duplicate-name handling.
Audit log — jsonl append per file. Test: one line per processed file, valid JSON.
Markdown report — all 11 required sections + invoice table with Unknown rules. Test: report contains sections, manual-review + error sections populate.
CLI + orchestrator — argparse with all flags, dry-run cut line, rich console summary. Test: dry-run writes no files but produces results.
README — purpose, privacy model, install, Tesseract on macOS, usage, dry-run, config, confidence interpretation, limitations, future work.
Run full test suite, fix, add examples/sample_invoice_summary.md.
Then (out of v1 scope, deferred): Phase 6 GUI (Streamlit/Textual), Phase 7 DOCX export, Phase 8 local LLM via Ollama as an optional classifier that augments — never replaces — the rule-based result.

My recommendation on two open choices (flagging rather than deciding for you):

pdfplumber over pypdf as the primary PDF reader — amounts often sit in tables and pdfplumber recovers them better. Small speed cost, worth it.
Add the routing + capabilities modules even though they're not in the original file list — they isolate the riskiest logic (manual-review decisions, missing-OCR handling) and keep cli.py thin.
Want me to proceed to build Phase 1 (skeleton, models, config, categories.yaml) next, or adjust the plan first?

Maybe you can reuse: https://github.com/thomassuedbroecker/docling_preprocessor_factory_public
Good idea — let me look at that repo to see what's reusable for the invoice sorter.

Web Fetchhttps://github.com/thomassuedbroecker/docling_preprocessor_factory_public
Fetched from https://github.com/thomassuedbroecker/docling_preprocessor_factory_public
Web Fetchhttps://github.com/thomassuedbroecker/docling_preprocessor_factory_public/blob/main/code/preprocess_app.py
Fetched from https://github.com/thomassuedbroecker/docling_preprocessor_factory_public/blob/main/code/preprocess_app.py
Web Fetchhttps://github.com/thomassuedbroecker/docling_preprocessor_factory_public/blob/main/README.md
Fetched from https://github.com/thomassuedbroecker/docling_preprocessor_factory_public/blob/main/README.md
There is also a UI app https://github.com/thomassuedbroecker/pdf_extraction_macos_public_version

---
use the tax input folder to get pdfs ... this pdfs are real user data and are not allowed to be shared and referenced in the code