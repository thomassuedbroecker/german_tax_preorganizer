"""Focused tests for GUI progress and cancellation controls."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from invoice_sorter.gui import MainWindow  # noqa: E402


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def test_progress_displays_completed_and_total_documents(app):
    window = MainWindow()

    window._on_progress(3, 8)

    assert window.progress.minimum() == 0
    assert window.progress.maximum() == 8
    assert window.progress.value() == 3
    assert window.progress.format() == "3 / 8 documents"
    window.close()


def test_stop_button_requests_worker_cancellation(app):
    class WorkerStub:
        cancelled = False

        def cancel(self):
            self.cancelled = True

    window = MainWindow()
    worker = WorkerStub()
    window._worker = worker
    window.stop_btn.setEnabled(True)

    window._on_stop()

    assert worker.cancelled is True
    assert window.stop_btn.isEnabled() is False
    assert "Stopping" in window.summary_label.text()
    window.close()
