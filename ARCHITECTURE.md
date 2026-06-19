# Architecture

## System Overview

Invoice Sorter is a **local-first, desktop-and-CLI invoice organizer** that classifies PDF/image documents, extracts metadata, and routes them into category folders. The system has two primary interfaces: a command-line tool and a PySide6 desktop GUI, both backed by a unified orchestration engine.

## High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                       User Interfaces                           │
├─────────────────────────────────────┬───────────────────────────┤
│   CLI (invoice-sorter)              │   GUI (invoice-sorter-gui)│
│   • argparse flags                  │   • PySide6 desktop app   │
│   • Run options validation          │   • Progress & drag-drop  │
│   • Report/audit/log output         │   • Category editor       │
└─────────────────────────────────────┴───────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│              Orchestrator (orchestrator.py)                      │
│  • Scan input folder for PDFs/images                            │
│  • Delegate to extraction adapter                               │
│  • Classify each document (confidence scoring)                  │
│  • Route to category folder (copy/move)                         │
│  • Collect results & summary for reporting                      │
└─────────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐
    │ Extraction  │   │ Classifier   │   │ File Operations  │
    │ Adapter     │   │ (Confidence) │   │ (Copy/Move/Log)  │
    │             │   │              │   │                  │
    │ • Docling   │   │ • Rule-based │   │ • Atomic writes  │
    │ • Light     │   │   scorer     │   │ • Dry-run mode   │
    │ • Fallback  │   │ • Metadata   │   │ • Error handling │
    └─────────────┘   │   matching   │   └──────────────────┘
                      └──────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│           Reporting & Audit (report.py, audit_log.py)          │
│  • Build Markdown summary for tax advisor                       │
│  • Write JSONL audit log (one JSON per document)                │
│  • Write performance metrics (extraction, classification time) │
└─────────────────────────────────────────────────────────────────┘
```

## Key Modules

### Core Pipeline

| Module | Responsibility |
|--------|-----------------|
| `orchestrator.py` | Main entry point; coordinates scan → extract → classify → route |
| `extraction_adapter.py` | Abstracts Docling and light backends; selects active backend at runtime |
| `classifier.py` | Rule-based invoice classification; returns category + confidence |
| `file_operations.py` | Copy/move/delete operations with dry-run safety and atomic writes |
| `scanner.py` | File system walk; detects supported formats (PDF, JPG, PNG, TIFF) |
| `metadata_extraction.py` | Parses extracted text for vendor, dates, amounts, currency, VAT, IBAN |
| `report.py` | Generates Markdown summary and collects run statistics |
| `audit_log.py` | Writes JSONL audit trail (one line per document) |
| `performance_log.py` | Tracks extraction/classification timing and token counts |

### Configuration & Models

| Module | Responsibility |
|--------|-----------------|
| `config.py` | Loads and validates `categories.yaml` (category names, keywords, vendors) |
| `models.py` | Data classes: `DocumentResult`, `ProcessingStatus`, `InvoiceMetadata`, etc. |
| `constants.py` | Defaults, status codes, currency/VAT patterns |

### CLI & GUI

| Module | Responsibility |
|--------|-----------------|
| `cli.py` | argparse entry point; reads flags, constructs `RunOptions`, calls orchestrator |
| `gui.py` | PySide6 desktop app; progress display, category editing, PDF/CSV export, agent client |

### AI Integration (Optional)

| Module | Responsibility |
|--------|-----------------|
| `ai_review.py` | Optional post-sort review using local Ollama; reads anonymized summary, returns text |
| `agent_service.py` | LangGraph agent REST server; `/api/executive-report-stream`, `/api/document-advice` endpoints |
| `agent_client.py` | HTTP client wrapper for agent endpoints; streaming and sync variants |

## Data Flow

### Typical Run

```
User invokes:
  invoice-sorter --input /path/to/pdfs --output /out --config categories.yaml

1. CLI parses arguments → RunOptions
2. Orchestrator scans /path/to/pdfs (recursive)
3. For each file (PDF/image):
   a. Extract text (Docling or light backend)
   b. Extract metadata (vendor, dates, amounts)
   c. Classify via rule-based scorer → category + confidence
   d. Copy file to /out/Sorted_Invoices/<category>/ (dry-run: skip copy)
4. Collect DocumentResult and RunSummary
5. Report:
   - Write /out/invoice_summary.md (category counts, manual review list)
   - Write /out/audit_log.jsonl (one JSON per document)
   - Write /out/performance_log.json (timing, token counts)
```

### GUI Workflow

```
User launches invoice-sorter-gui

1. Window initializes; agent REST server starts on 127.0.0.1:8080
2. User selects input/output folders, config, options
3. Click "Run" → Worker thread spawned (non-blocking)
4. Progress bar updates; live elapsed/ETA displayed
5. Run completes → results table populated
6. User can:
   - Double-click Category column → edit (QInputDialog dropdown or text)
   - Click "Edit Category" → re-trigger edit on selected row
   - Click "Undo Last Change" → revert last edit
   - Click "Export Corrections" → save as CSV
   - Click "Generate Exec PDF" → render summary as PDF
   - Click "Agent Exec Report" → stream report from LangGraph agent
   - Click "Open report" / "Open folder" / double-click source file
```

## Streaming Agent Integration

Added in recent release:

- **Server** (`agent_service.py`): new `/api/executive-report-stream` endpoint returns newline-delimited JSON chunks.
- **Client** (`agent_client.py`): `request_executive_report_stream()` generator yields chunks via urllib.
- **GUI** (`gui.py`): `ExecReportWorker` (QThread) consumes stream, emits chunks to modal dialog.

All agent communication is **local HTTP** (no external service required); LangGraph agent wraps Ollama for inference.

## Configuration

### Categories YAML

```yaml
categories:
  "Essen & Trinken":
    keywords: [restaurant, cafe, food]
    vendors: [RestaurantName]
  "Bürobedarf":
    keywords: [office, stationery]
    vendors: []

settings:
  manual_review_category: "Unklar / Manuell prüfen"
  confidence_threshold: 0.5
  default_currency: "EUR"
```

Loaded at startup; CLI and GUI both use the same loader (`config.load_config()`).

## Testing

- **Unit tests**: `tests/test_*.py` (pytest)
- **GUI tests**: offscreen rendering (QT_QPA_PLATFORM=offscreen)
- **Server endpoint tests**: start ephemeral server, mock internal handlers
- **Streaming tests**: mock urllib responses, verify ndjson parsing
- **CI**: GitHub Actions matrix (ubuntu/macos × Python 3.11/3.12)

Run tests:
```bash
.venv/bin/python -m pytest -q
```

## Privacy & Security

1. **No network uploads**: All processing is local.
2. **Dry-run by default**: Preview before any file is touched.
3. **Copy, not delete**: Original invoices are never removed.
4. **Metadata only**: Full invoice text is never logged or reported (only extracted fields).
5. **Optional AI review**: Ollama runs locally; anonymized summary sent (no full text).
6. **Offline mode**: Set `HF_HUB_OFFLINE=1` + `TRANSFORMERS_OFFLINE=1` after Docling warmup for guaranteed offline.

## Dependencies

### Core
- `pyyaml`: Config parsing
- `dataclasses`: Model definitions
- `pathlib`: File system operations

### Optional
- `docling` + `docling-pdf-backend`: Layout-aware PDF extraction
- `pdfplumber`, `pypdf`: Light PDF extraction
- `pytesseract` + `tesseract-ocr`: OCR for images
- `PySide6`: Desktop GUI
- `langgraph`, `langchain-core`: LangGraph agent framework
- `ollama`: Local LLM inference (via HTTP, not imported as library)

## Performance Characteristics

- **Extraction**: Docling ~5–20s per document (models loaded once); Light ~0.5–2s (depends on OCR).
- **Classification**: <100ms per document (rule-based, not ML).
- **File I/O**: ~100ms per document (copy speed depends on disk/network).
- **GUI responsiveness**: Worker thread ensures progress bar updates are live; long operations don't block UI.

## Future Considerations

1. **Batch category edits**: Bulk assign category to selected rows.
2. **Persist corrections**: Option to save edits back to results or reload from audit log.
3. **Custom extraction rules**: User-defined patterns for vendor/amount matching.
4. **DOCX export**: Alternative to Markdown report.
5. **Multi-language support**: Expand German/English metadata extraction.
6. **Cloud/network backends**: Optional remote orchestrator for shared servers.
