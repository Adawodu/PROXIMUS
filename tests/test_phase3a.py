"""Tests for Phase 3A: SQLite storage, migration, pagination, rate limiting,
per-resume voice, and the summary field."""

from __future__ import annotations

import json
from datetime import datetime

import pytest
from fastapi import HTTPException

from proximus.api.main import _check_outbound_rate_limit, _outbound_call_times
from proximus.config import get_settings
from proximus.context.calls import CallManager, CallRecord
from proximus.context.resume import Resume, ResumeManager


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _record(call_id: str, hour: int = 12, summary: str | None = None) -> CallRecord:
    return CallRecord(
        id=call_id,
        room_name="room",
        resume_id=None,
        candidate_name="Jane",
        caller_phone=None,
        direction="inbound",
        started_at=datetime(2026, 1, 1, hour, 0, 0),
        summary=summary,
    )


# --- Pagination + count --------------------------------------------------------


def test_call_pagination_and_count(tmp_path):
    m = CallManager(storage_dir=str(tmp_path / "calls"))
    for i in range(5):
        m.save_call(_record(f"c{i}", hour=i))
    assert m.count_calls() == 5
    page = m.list_calls(limit=2, offset=0)
    assert [c.id for c in page] == ["c4", "c3"]  # most recent first
    assert [c.id for c in m.list_calls(limit=2, offset=2)] == ["c2", "c1"]
    assert len(m.list_calls()) == 5  # no limit -> all


def test_resume_pagination_and_count(tmp_path):
    m = ResumeManager(storage_dir=str(tmp_path / "resumes"))
    for i in range(3):
        m._save_resume(Resume(id=f"r{i}", candidate_name=f"C{i}", content="x", file_path=""))
    assert m.count_resumes() == 3
    assert len(m.list_resumes(limit=1)) == 1


# --- Legacy JSON migration -----------------------------------------------------


def test_legacy_call_json_is_migrated(tmp_path):
    calls_dir = tmp_path / "calls"
    calls_dir.mkdir()
    legacy = _record("legacy1").to_dict()
    legacy.pop("summary")  # simulate a pre-summary record
    (calls_dir / "legacy1.json").write_text(json.dumps(legacy), encoding="utf-8")

    m = CallManager(storage_dir=str(calls_dir))
    loaded = m.get_call("legacy1")
    assert loaded is not None
    assert loaded.summary is None
    assert m.count_calls() == 1


def test_legacy_registry_is_migrated(tmp_path):
    resumes_dir = tmp_path / "resumes"
    resumes_dir.mkdir()
    resume = Resume(id="r1", candidate_name="Jane", content="Python", file_path="")
    registry = {"resumes": {"r1": resume.to_dict()}, "phone_links": {"+14155550100": "r1"}}
    (resumes_dir / "registry.json").write_text(json.dumps(registry), encoding="utf-8")

    m = ResumeManager(storage_dir=str(resumes_dir))
    assert m.get_resume("r1") is not None
    assert m.get_resume_by_phone("+14155550100") is not None


# --- Rate limiter --------------------------------------------------------------


def test_outbound_rate_limiter(monkeypatch):
    _outbound_call_times.clear()
    monkeypatch.setenv("OUTBOUND_RATE_LIMIT_PER_MIN", "2")
    get_settings.cache_clear()
    _check_outbound_rate_limit()
    _check_outbound_rate_limit()
    with pytest.raises(HTTPException) as exc:
        _check_outbound_rate_limit()
    assert exc.value.status_code == 429
    _outbound_call_times.clear()


def test_rate_limiter_disabled_when_zero(monkeypatch):
    _outbound_call_times.clear()
    monkeypatch.setenv("OUTBOUND_RATE_LIMIT_PER_MIN", "0")
    get_settings.cache_clear()
    for _ in range(50):
        _check_outbound_rate_limit()  # never raises when disabled
    _outbound_call_times.clear()


# --- Per-resume voice ----------------------------------------------------------


def test_set_voice(tmp_path):
    m = ResumeManager(storage_dir=str(tmp_path / "resumes"))
    m._save_resume(Resume(id="r1", candidate_name="Jane", content="x", file_path=""))
    updated = m.set_voice("r1", "voice-xyz")
    assert updated is not None and updated.voice == "voice-xyz"
    assert m.get_resume("r1").voice == "voice-xyz"
    assert m.set_voice("missing", "v") is None


# --- Summary field round-trip --------------------------------------------------


def test_summary_roundtrip():
    restored = CallRecord.from_dict(_record("x", summary="A short summary.").to_dict())
    assert restored.summary == "A short summary."
