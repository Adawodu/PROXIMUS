"""Call record and transcript management."""

from __future__ import annotations

import json as _json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

_logger = logging.getLogger(__name__)


@dataclass
class CallTranscriptEntry:
    """A single turn in a call transcript."""

    role: str  # "user" | "agent"
    text: str
    timestamp: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CallTranscriptEntry:
        return cls(**data)


@dataclass
class CallRecord:
    """A completed call with transcript."""

    id: str
    room_name: str
    resume_id: str | None
    candidate_name: str
    caller_phone: str | None
    direction: str  # "inbound" | "outbound"
    started_at: datetime
    ended_at: datetime | None = None
    transcript: list[CallTranscriptEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["started_at"] = self.started_at.isoformat()
        d["ended_at"] = self.ended_at.isoformat() if self.ended_at else None
        d["transcript"] = [e.to_dict() for e in self.transcript]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> CallRecord:
        data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("ended_at"):
            data["ended_at"] = datetime.fromisoformat(data["ended_at"])
        data["transcript"] = [CallTranscriptEntry.from_dict(e) for e in data.get("transcript", [])]
        return cls(**data)

    @staticmethod
    def generate_id() -> str:
        return uuid.uuid4().hex[:12]


class CallManager:
    """Manages call record storage and retrieval."""

    def __init__(self, storage_dir: str = "./data/calls"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_call(self, record: CallRecord) -> None:
        """Save a call record to disk."""
        path = self.storage_dir / f"{record.id}.json"
        path.write_text(_json.dumps(record.to_dict(), indent=2), encoding="utf-8")
        _logger.info(f"Saved call record {record.id} ({len(record.transcript)} turns)")

    def get_call(self, call_id: str) -> CallRecord | None:
        """Retrieve a call record by ID."""
        path = self.storage_dir / f"{call_id}.json"
        if not path.exists():
            return None
        try:
            data = _json.loads(path.read_text(encoding="utf-8"))
            return CallRecord.from_dict(data)
        except Exception as exc:
            _logger.warning(f"Failed to load call {call_id}: {exc}")
            return None

    def list_calls(self) -> list[CallRecord]:
        """List all call records, sorted by date descending."""
        records: list[CallRecord] = []
        for path in self.storage_dir.glob("*.json"):
            try:
                data = _json.loads(path.read_text(encoding="utf-8"))
                records.append(CallRecord.from_dict(data))
            except Exception as exc:
                _logger.warning(f"Failed to load call {path.stem}: {exc}")
        records.sort(key=lambda r: r.started_at, reverse=True)
        return records
