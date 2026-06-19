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

from PySide6.QtCore import QObject, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
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

    def __init__(self, options: RunOptions) -> None:
        super().__init__()
        self.options = options

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
        form.addWidget(QLabel("Ollama model"), 3, 0)
        form.addWidget(self.ai_model_edit, 3, 1)
        form.addWidget(QLabel("Ollama URL"), 4, 0)
        form.addWidget(self.ai_url_edit, 4, 1)
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
        self.open_report_btn = QPushButton("Open report")
        self.open_report_btn.clicked.connect(self._open_report)
        self.open_report_btn.setEnabled(False)
        self.open_folder_btn = QPushButton("Open output folder")
        self.open_folder_btn.clicked.connect(self._open_folder)
        self.open_folder_btn.setEnabled(False)
        run_row.addWidget(self.run_btn)
        run_row.addWidget(self.open_report_btn)
        run_row.addWidget(self.open_folder_btn)
        run_row.addStretch(1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
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
    def _browse_btn(self, target: QLineEdit, *, folder: bool) -> QPushButton:
        btn = QPushButton("Browse…")

        def choose() -> None:
            if folder:
                path = QFileDialog.getExistingDirectory(self, "Select folder")
            else:
                path, _ = QFileDialog.getOpenFileName(
                    self, "Select config", "", "YAML/JSON (*.yaml *.yml *.json)"
                )
            if path:
                target.setText(path)

        btn.clicked.connect(choose)
        return btn

    def _set_busy(self, busy: bool) -> None:
        self.run_btn.setEnabled(not busy)
        self.progress.setVisible(busy)

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

        manual = sum(1 for r in results
                     if r.status == ProcessingStatus.MANUAL_REVIEW
                     or r.category == summary.manual_review_category)
        failed = sum(1 for r in results if r.status == ProcessingStatus.FAILED)
        mode = "DRY RUN" if summary.dry_run else ("MOVE" if self.move.isChecked() else "COPY")
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
                    item.setBackground(QColor(255, 246, 214))
                elif col == 6 and r.confidence >= 0.9:
                    item.setBackground(QColor(224, 245, 224))
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)

    def _open_report(self) -> None:
        if self._last_output:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self._last_output / REPORT_NAME))
            )

    def _open_folder(self) -> None:
        if self._last_output:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_output)))


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
