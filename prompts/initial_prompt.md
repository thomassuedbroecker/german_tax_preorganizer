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
