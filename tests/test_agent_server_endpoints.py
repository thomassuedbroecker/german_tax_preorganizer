"""Server-side endpoint tests for the agent REST service."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
import time

import pytest

# The in-app agent service needs the optional [agent] extra (langgraph). Skip
# these tests cleanly when it is not installed (e.g. the minimal CI job).
pytest.importorskip("langgraph")

from invoice_sorter import agent_service


def start_handle():
    handle = agent_service.start_agent_server(host="127.0.0.1", port=0)
    # wait for server to be ready
    time.sleep(0.1)
    return handle


def test_executive_report_stream_endpoint(monkeypatch):
    # mock the internal report generator
    def fake_run_executive_report(summary, base_url=None, model=None, temperature=0.2):
        return "This is a streamed report. " * 5

    monkeypatch.setattr(agent_service, "run_executive_report", fake_run_executive_report)

    handle = start_handle()
    try:
        port = handle.server.server_address[1]
        url = f"http://127.0.0.1:{port}/api/executive-report-stream"
        payload = json.dumps({"summary": {"processed": 1}}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            chunks = []
            for raw in resp:
                line = raw.decode("utf-8").strip()
                if not line:
                    continue
                obj = json.loads(line)
                chunks.append(obj.get("chunk", ""))
        assert "This is a streamed report." in "".join(chunks)
    finally:
        handle.shutdown()


def test_document_advice_endpoint(monkeypatch):
    def fake_run_document_advice(document, base_url=None, model=None, temperature=0.2):
        return "Advice for document"

    monkeypatch.setattr(agent_service, "run_document_advice", fake_run_document_advice)

    handle = start_handle()
    try:
        port = handle.server.server_address[1]
        url = f"http://127.0.0.1:{port}/api/document-advice"
        payload = json.dumps({"document": {"file_name": "a.pdf"}}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        assert data.get("advice") == "Advice for document"
    finally:
        handle.shutdown()
