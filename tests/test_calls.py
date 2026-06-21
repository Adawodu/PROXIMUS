"""Tests for call record storage and serialization (no API keys required)."""

from __future__ import annotations

from datetime import datetime

import pytest

from proximus.context.calls import CallManager, CallRecord, CallTranscriptEntry


@pytest.fixture
def manager(tmp_path):
    return CallManager(storage_dir=str(tmp_path / "calls"))


def make_record(call_id: str = "call-1") -> CallRecord:
    return CallRecord(
        id=call_id,
        room_name="proximus-outbound-abc",
        resume_id="res-1",
        candidate_name="Jane Doe",
        caller_phone="+14155550100",
        direction="outbound",
        started_at=datetime(2026, 1, 1, 12, 0, 0),
        ended_at=datetime(2026, 1, 1, 12, 5, 0),
        transcript=[
            CallTranscriptEntry(role="agent", text="Hello, this is Jane.", timestamp=1.0),
            CallTranscriptEntry(role="user", text="Hi Jane, thanks for calling.", timestamp=2.0),
        ],
    )


class TestSerialization:
    def test_record_roundtrip(self):
        record = make_record()
        restored = CallRecord.from_dict(record.to_dict())
        assert restored.id == record.id
        assert restored.direction == "outbound"
        assert restored.started_at == record.started_at
        assert restored.ended_at == record.ended_at
        assert len(restored.transcript) == 2
        assert restored.transcript[0].role == "agent"

    def test_handles_missing_ended_at(self):
        record = make_record()
        record.ended_at = None
        restored = CallRecord.from_dict(record.to_dict())
        assert restored.ended_at is None

    def test_generate_id_is_unique(self):
        assert CallRecord.generate_id() != CallRecord.generate_id()


class TestCallManager:
    def test_save_and_get(self, manager):
        record = make_record()
        manager.save_call(record)
        loaded = manager.get_call(record.id)
        assert loaded is not None
        assert loaded.candidate_name == "Jane Doe"
        assert len(loaded.transcript) == 2

    def test_get_missing_returns_none(self, manager):
        assert manager.get_call("nope") is None

    def test_list_sorted_by_started_at_desc(self, manager):
        older = make_record("old")
        older.started_at = datetime(2026, 1, 1, 9, 0, 0)
        newer = make_record("new")
        newer.started_at = datetime(2026, 1, 1, 18, 0, 0)
        manager.save_call(older)
        manager.save_call(newer)

        calls = manager.list_calls()
        assert [c.id for c in calls] == ["new", "old"]
