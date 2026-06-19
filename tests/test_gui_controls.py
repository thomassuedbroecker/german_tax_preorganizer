"""Focused tests for GUI progress and cancellation controls."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from invoice_sorter.gui import MainWindow  # noqa: E402
from invoice_sorter.models import DocumentResult, ProcessingStatus  # noqa: E402
from invoice_sorter.report import RunSummary  # noqa: E402


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def test_progress_displays_completed_and_total_documents(app):
    window = MainWindow()

    assert window.ai_prompt_edit.text().endswith("config/ai_review_prompt.txt")
    assert window.ai_temperature.value() == 0.2

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


def test_agent_server_starts_on_window_init(app, monkeypatch):
    class DummyHandle:
        def __init__(self):
            self.shutdown_called = False

        def shutdown(self):
            self.shutdown_called = True

    dummy_handle = DummyHandle()
    started = {}

    def fake_start_agent_server(host, port):
        started["host"] = host
        started["port"] = port
        return dummy_handle

    monkeypatch.setattr("invoice_sorter.gui.start_agent_server", fake_start_agent_server)

    window = MainWindow()

    assert window._agent_handle is dummy_handle
    assert started["host"] == "127.0.0.1"
    assert started["port"] == 8080
    assert window.agent_status_label.text() == "Agent server: http://127.0.0.1:8080"

    window.close()
    assert dummy_handle.shutdown_called is True


def test_manual_review_rows_use_red_background_and_white_text(app):
    window = MainWindow()
    result = DocumentResult(source_path=Path("anonymous.pdf"))
    result.category = "Unklar / Manuell prüfen"
    result.status = ProcessingStatus.MANUAL_REVIEW

    window._on_finished([result], RunSummary(total_scanned=1))

    item = window.table.item(0, 0)
    assert item.background().color().getRgb()[:3] == (185, 28, 28)
    assert item.foreground().color().getRgb()[:3] == (255, 255, 255)
    window.close()
