"""End-to-end API tests using FastAPI's TestClient.

The resume/call managers are swapped for tmp-dir-backed instances so these
tests never touch ./data.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

import proximus.agent.outbound  # noqa: F401 — import on the main thread so LiveKit

# plugins register before TestClient runs the outbound handler in a worker thread.
import proximus.api.main as main
from proximus.api.main import app
from proximus.config import get_settings
from proximus.context.calls import CallManager, CallRecord
from proximus.context.resume import ResumeManager

SAMPLE = b"Jane Doe\nSenior Engineer\n\n6 years of Python and FastAPI.\n"


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setattr(main, "_resume_manager", ResumeManager(storage_dir=str(tmp_path / "r")))
    monkeypatch.setattr(main, "_call_manager", CallManager(storage_dir=str(tmp_path / "c")))
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _upload(client) -> str:
    resp = client.post("/resumes", files={"file": ("jane.txt", SAMPLE, "text/plain")})
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


# --- Resumes CRUD --------------------------------------------------------------


def test_health(client):
    assert client.get("/health").json()["status"] == "healthy"


def test_resume_upload_list_get_delete(client):
    rid = _upload(client)

    listing = client.get("/resumes").json()
    assert listing["total"] == 1
    assert listing["resumes"][0]["candidate_name"] == "Jane Doe"
    assert listing["resumes"][0]["voice"] == ""

    got = client.get(f"/resumes/{rid}")
    assert got.status_code == 200

    ctx = client.get(f"/resumes/{rid}/context").json()
    assert "system_prompt" in ctx and "Jane Doe" in ctx["system_prompt"]

    assert client.delete(f"/resumes/{rid}").status_code == 200
    assert client.get("/resumes").json()["total"] == 0
    assert client.get(f"/resumes/{rid}").status_code == 404


def test_patch_resume_voice(client):
    rid = _upload(client)
    resp = client.patch(f"/resumes/{rid}", json={"voice": "voice-abc"})
    assert resp.status_code == 200
    assert resp.json()["voice"] == "voice-abc"
    assert client.patch("/resumes/missing", json={"voice": "x"}).status_code == 404


# --- Phone links ---------------------------------------------------------------


def test_phone_link_lifecycle(client):
    rid = _upload(client)
    created = client.post("/phone-links", json={"phone": "(415) 555-0100", "resume_id": rid})
    assert created.status_code == 200
    assert created.json()["phone"] == "+14155550100"

    assert client.get("/phone-links").json()["total"] == 1
    assert client.get("/phone-links/+14155550100").status_code == 200
    assert client.get(f"/resumes/{rid}/phones").json()["phones"] == ["+14155550100"]

    assert client.delete("/phone-links/+14155550100").status_code == 200
    assert client.delete("/phone-links/+14155550100").status_code == 404


def test_phone_link_unknown_resume_404(client):
    resp = client.post("/phone-links", json={"phone": "+14155550100", "resume_id": "nope"})
    assert resp.status_code == 404


# --- Calls ---------------------------------------------------------------------


def test_calls_list_and_detail(client):
    main._call_manager.save_call(
        CallRecord(
            id="call1",
            room_name="room",
            resume_id=None,
            candidate_name="Jane",
            caller_phone=None,
            direction="inbound",
            started_at=datetime(2026, 1, 1, 12, 0, 0),
            summary="Discussed the role.",
        )
    )
    listing = client.get("/calls").json()
    assert listing["total"] == 1
    assert listing["calls"][0]["summary"] == "Discussed the role."

    detail = client.get("/calls/call1").json()
    assert detail["id"] == "call1"
    assert detail["summary"] == "Discussed the role."
    assert client.get("/calls/missing").status_code == 404


# --- Outbound guard paths (no LiveKit) -----------------------------------------


def test_outbound_unknown_resume_404(client):
    resp = client.post("/calls/outbound", json={"phone": "+14155550100", "resume_id": "nope"})
    assert resp.status_code == 404


def test_outbound_caller_id_requires_connection_id(client):
    rid = _upload(client)
    resp = client.post(
        "/calls/outbound",
        json={"phone": "+14155550100", "resume_id": rid, "caller_id": "+12125550123"},
    )
    assert resp.status_code == 400
    assert "TELNYX_CREDENTIAL_CONNECTION_ID" in resp.json()["detail"]
