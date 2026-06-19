"""PySide6 desktop UI for the invoice sorter.

A thin window on top of :func:`invoice_sorter.orchestrator.run`. The heavy work
runs in a worker thread so the window stays responsive (Docling can be slow).

Privacy: this is a local desktop app showing your own data on your own machine.
Dry-run is ON by default so the first click never copies anything.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QTextDocument
from PySide6.QtPrintSupport import QPrinter
import csv
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .ai_review import DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_URL
from .config import ConfigError, load_config
from .extraction_adapter import active_backend
from .models import UNKNOWN, ProcessingStatus
from .orchestrator import RunOptions, run
from .report import REPORT_NAME

_DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "categories.yaml"
_DEFAULT_AI_PROMPT = Path(__file__).resolve().parents[2] / "config" / "ai_review_prompt.txt"

_COLUMNS = ["File", "Category", "Vendor", "Invoice Date", "Gross", "Currency",
            "Confidence", "Status", "Notes"]


def _cell(value) -> str:
    if value is None:
        return UNKNOWN
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


class Worker(QObject):
    """Runs the pipeline off the UI thread."""

    finished = Signal(object, object)  # (results, summary)
    failed = Signal(str)
    progress = Signal(int, int)  # (completed, total)

    def __init__(self, options: RunOptions) -> None:
        super().__init__()
        self.options = options
        self._cancel_requested = Event()
        self.options.progress_callback = self.progress.emit
        self.options.cancel_check = self._cancel_requested.is_set

    def cancel(self) -> None:
        self._cancel_requested.set()

    def run(self) -> None:
        try:
            results, summary = run(self.options)
            self.finished.emit(results, summary)
        except Exception as exc:  # surfaced in a dialog, never crashes the app
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Invoice Sorter")
        self.resize(1040, 640)
        self._thread: QThread | None = None
        self._worker: Worker | None = None
        self._last_output: Path | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- form -------------------------------------------------------
        form = QGridLayout()
        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()
        self.config_edit = QLineEdit(str(_DEFAULT_CONFIG))
        form.addWidget(QLabel("Input folder"), 0, 0)
        form.addWidget(self.input_edit, 0, 1)
        form.addWidget(self._browse_btn(self.input_edit, folder=True), 0, 2)
        form.addWidget(QLabel("Output folder"), 1, 0)
        form.addWidget(self.output_edit, 1, 1)
        form.addWidget(self._browse_btn(self.output_edit, folder=True), 1, 2)
        form.addWidget(QLabel("Config (categories.yaml)"), 2, 0)
        form.addWidget(self.config_edit, 2, 1)
        form.addWidget(self._browse_btn(self.config_edit, folder=False), 2, 2)
        self.ai_model_edit = QLineEdit(DEFAULT_OLLAMA_MODEL)
        self.ai_url_edit = QLineEdit(DEFAULT_OLLAMA_URL)
        self.ai_prompt_edit = QLineEdit(str(_DEFAULT_AI_PROMPT))
        self.ai_temperature = QDoubleSpinBox()
        self.ai_temperature.setRange(0.0, 2.0)
        self.ai_temperature.setDecimals(2)
        self.ai_temperature.setSingleStep(0.1)
        self.ai_temperature.setValue(0.2)
        form.addWidget(QLabel("Ollama model"), 3, 0)
        form.addWidget(self.ai_model_edit, 3, 1)
        form.addWidget(QLabel("Ollama URL"), 4, 0)
        form.addWidget(self.ai_url_edit, 4, 1)
        form.addWidget(QLabel("AI temperature"), 5, 0)
        form.addWidget(self.ai_temperature, 5, 1)
        form.addWidget(QLabel("AI review prompt"), 6, 0)
        form.addWidget(self.ai_prompt_edit, 6, 1)
        form.addWidget(
            self._browse_btn(
                self.ai_prompt_edit,
                folder=False,
                file_filter="Prompt templates (*.txt *.md);;All files (*)",
            ),
            6,
            2,
        )
        root.addLayout(form)

        # --- options ----------------------------------------------------
        opts = QHBoxLayout()
        self.dry_run = QCheckBox("Dry run (no files copied)")
        self.dry_run.setChecked(True)
        self.recursive = QCheckBox("Recursive")
        self.recursive.setChecked(True)
        self.move = QCheckBox("Move instead of copy")
        self.ai_review = QCheckBox("Local AI review")
        self.backend_combo = QComboBox()
        self.backend_combo.addItem(f"Auto ({active_backend()})", "auto")
        self.backend_combo.addItem("Docling", "docling")
        self.backend_combo.addItem("Light", "light")
        opts.addWidget(self.dry_run)
        opts.addWidget(self.recursive)
        opts.addWidget(self.move)
        opts.addWidget(self.ai_review)
        opts.addStretch(1)
        opts.addWidget(QLabel("Backend"))
        opts.addWidget(self.backend_combo)
        root.addLayout(opts)

        # --- run row ----------------------------------------------------
        run_row = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._on_run)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._on_stop)
        self.stop_btn.setEnabled(False)
        self.open_report_btn = QPushButton("Open report")
        self.open_report_btn.clicked.connect(self._open_report)
        self.open_report_btn.setEnabled(False)
        self.open_folder_btn = QPushButton("Open output folder")
        self.open_folder_btn.clicked.connect(self._open_folder)
        self.open_folder_btn.setEnabled(False)
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self._export_table_csv)
        self.export_csv_btn.setEnabled(False)
        self.exec_pdf_btn = QPushButton("Generate Exec PDF")
        self.exec_pdf_btn.clicked.connect(self._generate_exec_pdf)
        self.exec_pdf_btn.setEnabled(False)
        run_row.addWidget(self.run_btn)
        run_row.addWidget(self.stop_btn)
        run_row.addWidget(self.open_report_btn)
        run_row.addWidget(self.export_csv_btn)
        run_row.addWidget(self.exec_pdf_btn)
        run_row.addWidget(self.open_folder_btn)
        run_row.addStretch(1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setMinimumWidth(180)
        self.progress.hide()
        run_row.addWidget(self.progress)
        root.addLayout(run_row)

        # --- summary ----------------------------------------------------
        self.summary_label = QLabel("Pick an input folder and click Run.")
        root.addWidget(self.summary_label)

        # --- table ------------------------------------------------------
        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        root.addWidget(self.table, 1)

    # --- helpers --------------------------------------------------------
    def _browse_btn(
        self,
        target: QLineEdit,
        *,
        folder: bool,
        file_filter: str = "YAML/JSON (*.yaml *.yml *.json)",
    ) -> QPushButton:
        btn = QPushButton("Browse…")

        def choose() -> None:
            if folder:
                path = QFileDialog.getExistingDirectory(self, "Select folder")
            else:
                path, _ = QFileDialog.getOpenFileName(
                    self, "Select file", "", file_filter
                )
            if path:
                target.setText(path)

        btn.clicked.connect(choose)
        return btn

    def _set_busy(self, busy: bool) -> None:
        self.run_btn.setEnabled(not busy)
        self.stop_btn.setEnabled(busy)
        if busy:
            self.progress.setRange(0, 0)
            self.progress.setFormat("Preparing documents…")
        self.progress.setVisible(busy)

    def _on_progress(self, completed: int, total: int) -> None:
        maximum = max(total, 1)
        self.progress.setRange(0, maximum)
        self.progress.setValue(completed if total else maximum)
        self.progress.setFormat(f"{completed} / {total} documents")

    def _on_stop(self) -> None:
        if self._worker is None:
            return
        self._worker.cancel()
        self.stop_btn.setEnabled(False)
        self.summary_label.setText("Stopping after the current document…")

    # --- actions --------------------------------------------------------
    def _on_run(self) -> None:
        input_dir = Path(self.input_edit.text().strip()).expanduser()
        output_dir = Path(self.output_edit.text().strip()).expanduser()

        if not input_dir.is_dir():
            QMessageBox.warning(self, "Invalid input", "Input folder does not exist.")
            return
        if not output_dir.name:
            QMessageBox.warning(self, "Missing output", "Choose an output folder.")
            return
        try:
            config = load_config(self.config_edit.text().strip() or str(_DEFAULT_CONFIG))
        except ConfigError as exc:
            QMessageBox.critical(self, "Config error", str(exc))
            return

        options = RunOptions(
            input_dir=input_dir,
            output_dir=output_dir,
            config=config,
            dry_run=self.dry_run.isChecked(),
            recursive=self.recursive.isChecked(),
            move=self.move.isChecked(),
            extraction_backend=self.backend_combo.currentData(),
            ai_review=self.ai_review.isChecked(),
            ai_model=self.ai_model_edit.text().strip() or DEFAULT_OLLAMA_MODEL,
            ai_base_url=self.ai_url_edit.text().strip() or DEFAULT_OLLAMA_URL,
            ai_prompt_path=(
                Path(self.ai_prompt_edit.text().strip()).expanduser()
                if self.ai_prompt_edit.text().strip()
                else None
            ),
            ai_temperature=self.ai_temperature.value(),
        )
        self._last_output = output_dir

        self._set_busy(True)
        self.summary_label.setText("Working… (Docling can take a while on first run)")

        self._thread = QThread()
        self._worker = Worker(options)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.start()

    def _on_failed(self, message: str) -> None:
        self._set_busy(False)
        QMessageBox.critical(self, "Run failed", message)
        self.summary_label.setText("Run failed.")

    def _on_finished(self, results, summary) -> None:
        self._set_busy(False)
        self.open_report_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(True)
        self.export_csv_btn.setEnabled(True)
        self.exec_pdf_btn.setEnabled(True)
        # Save for later export actions
        self._last_results = results
        self._last_summary = summary

        manual = sum(1 for r in results
                     if r.status == ProcessingStatus.MANUAL_REVIEW
                     or r.category == summary.manual_review_category)
        failed = sum(1 for r in results if r.status == ProcessingStatus.FAILED)
        mode = "DRY RUN" if summary.dry_run else ("MOVE" if self.move.isChecked() else "COPY")
        if summary.cancelled:
            mode = f"CANCELLED {mode}"
        self.summary_label.setText(
            f"<b>{mode}</b> · scanned {summary.total_scanned} · processed "
            f"{len(results)} · sorted {len(results) - manual - failed} · "
            f"review {manual} · failed {failed} · unsupported "
            f"{len(summary.unsupported_files)}"
        )

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            m = r.metadata
            values = [
                r.source_path.name, r.category, _cell(m.vendor), _cell(m.invoice_date),
                _cell(m.gross_amount), _cell(m.currency), f"{r.confidence:.2f}",
                r.status.value, "; ".join(r.notes),
            ]
            is_manual = (r.status == ProcessingStatus.MANUAL_REVIEW
                         or r.category == summary.manual_review_category)
            is_failed = r.status == ProcessingStatus.FAILED
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if is_failed:
                    item.setBackground(QColor(255, 224, 224))
                elif is_manual:
                    item.setBackground(QColor(185, 28, 28))
                    item.setForeground(QColor(255, 255, 255))
                # Confidence column (col 6): exact 1.0 -> dark green + white text,
                # high confidence >= 0.9 -> light green.
                elif col == 6 and r.confidence >= 0.9999:
                    item.setBackground(QColor(0, 100, 0))
                    item.setForeground(QColor(255, 255, 255))
                elif col == 6 and r.confidence >= 0.9:
                    item.setBackground(QColor(224, 245, 224))
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)

    def _generate_exec_pdf(self) -> None:
        if not getattr(self, "_last_results", None) or not getattr(self, "_last_summary", None):
            QMessageBox.warning(self, "No data", "Run the sorter first to generate a report.")
            return
        default_path = str(self._last_output / "invoice_summary_exec.pdf") if self._last_output else ""
        path, _ = QFileDialog.getSaveFileName(self, "Save executive PDF", default_path, "PDF files (*.pdf);;All files (*)")
        if not path:
            return
        try:
            from .report import build_report

            md = build_report(self._last_results, self._last_summary)
            # Simple rendering: wrap markdown in <pre> to keep formatting.
            html = (
                '<html><head><meta charset="utf-8"><style>body{font-family: "Helvetica", "Arial", sans-serif; padding:20px;} pre{white-space:pre-wrap; font-family: "Helvetica", "Arial", sans-serif;}</style></head><body>'
                f"<h1>Executive Invoice Summary</h1><pre>{md}</pre></body></html>"
            )
            doc = QTextDocument()
            doc.setHtml(html)
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            doc.print(printer)
            QMessageBox.information(self, "PDF saved", f"Executive PDF written to {path}")
        except Exception as exc:
            QMessageBox.critical(self, "PDF generation failed", str(exc))

    def _open_report(self) -> None:
        if self._last_output:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self._last_output / REPORT_NAME))
            )

    def _open_folder(self) -> None:
        if self._last_output:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_output)))

    def _export_table_csv(self) -> None:
        # Prompt for save location and write current table contents as CSV.
        default_path = (
            str(self._last_output / "invoice_table.csv") if self._last_output else ""
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "Export table to CSV", default_path, "CSV files (*.csv);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                # header
                writer.writerow(_COLUMNS)
                for row in range(self.table.rowCount()):
                    row_values = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_values.append(item.text() if item is not None else "")
                    writer.writerow(row_values)
            QMessageBox.information(self, "Export complete", f"Wrote CSV to {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
