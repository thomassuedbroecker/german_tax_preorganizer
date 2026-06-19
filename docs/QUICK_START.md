# Quick Start

Fast path for running the invoice sorter locally.

## 1. Create the Environment

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[light,test]"
```

For the desktop app:

```bash
.venv/bin/pip install -e ".[gui]"
```

For Docling-quality amount/table extraction:

```bash
pip install -e ".[docling]"
```

## 2. Check the Backend

```bash
python -c "from invoice_sorter.extraction_adapter import active_backend; print(active_backend())"
```

Backend choices when running:

- `auto`: use Docling if available, otherwise light extraction.
- `docling`: prefer Docling with light fallback.
- `light`: skip Docling and use pdfplumber/pypdf/Tesseract.

## 3. Run a Dry Run

Use an output directory outside the repo when processing private invoices.

```bash
invoice-sorter \
  --input "/path/to/invoices" \
  --output "/private/tmp/invoice-sorter-out" \
  --config "config/categories.yaml" \
  --backend auto \
  --dry-run
```

Dry run writes:

- `/private/tmp/invoice-sorter-out/invoice_summary.md`
- `/private/tmp/invoice-sorter-out/audit_log.jsonl`
- `/private/tmp/invoice-sorter-out/performance_log.json`

It does not copy or move invoice files.

## 4. Review Results

Open `invoice_summary.md` and check:

- Category counts
- Files routed to `Unklar / Manuell prüfen`
- Extracted dates, invoice numbers, amounts, and confidence notes

If results look good, rerun without `--dry-run`:

```bash
invoice-sorter \
  --input "/path/to/invoices" \
  --output "/private/tmp/invoice-sorter-out" \
  --config "config/categories.yaml" \
  --backend auto
```

Default behavior copies files into `Sorted_Invoices/<Category>/`. Add `--move`
only if you intentionally want to move originals.

## 5. Use the GUI

Recommended: activate the project virtual environment, then launch the GUI:

```bash
source .venv/bin/activate
invoice-sorter-gui
```

The virtual environment is required because it contains PySide6 and the installed
application. It is not a background service; activation only selects its Python
and commands for the current shell.

Without activating it, run the executable explicitly from the same environment:

```bash
.venv/bin/invoice-sorter-gui
```

Module fallback:

```bash
.venv/bin/python -m invoice_sorter.gui
```

If the shell reports `command not found`, activate `.venv` or use the explicit
`.venv/bin/invoice-sorter-gui` command above.

In the app:

1. Pick input and output folders.
2. Pick the config file.
3. Leave Dry run enabled for the first pass.
4. Choose backend: Auto, Docling, or Light.
5. Click Run.

The progress bar shows how many documents have been inspected. Click **Stop** to
cancel after the current document; partial report, audit, and performance logs
are still written.

## 6. Improve Local Categories

To generate a git-ignored local config from your own invoice folder:

```bash
python scripts/suggest_local_config.py \
  --input "/path/to/invoices" \
  --base-config config/categories.yaml \
  --out config/categories.local.yaml
```

The script prints counts only. Private vendor tokens are written to the local
config file, which must not be committed.

Then run with:

```bash
invoice-sorter \
  --input "/path/to/invoices" \
  --output "/private/tmp/invoice-sorter-out" \
  --config config/categories.local.yaml \
  --backend auto \
  --dry-run
```

## 7. Add a Local AI Review

If Ollama is running locally, add an AI-generated sorting review to the Markdown
report:

```bash
invoice-sorter \
  --input "/path/to/invoices" \
  --output "/private/tmp/invoice-sorter-out" \
  --backend auto \
  --dry-run \
  --ai-review \
  --ai-model llama3.2
```

The AI review runs after sorting. It does not change categories, copy files, or
replace the rule-based classifier. It receives aggregate counts and extracted
metadata only, never full invoice text.

Ollama inference duration and prompt/output token counts are shown in the report
and stored in `performance_log.json`. The same log includes anonymized
per-document extraction and processing times.

## 8. Offline Docling Run

After Docling models are warmed up, enforce offline mode:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
invoice-sorter \
  --input "/path/to/invoices" \
  --output "/private/tmp/invoice-sorter-out" \
  --backend docling \
  --dry-run
```

## 9. Verify the Project

```bash
.venv/bin/python -m pytest -q
```
