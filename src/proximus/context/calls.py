"""Call record and transcript management (SQLite-backed).

Records are stored in a SQLite database (``<storage_dir>/calls.db``). Legacy
per-call ``*.json`` files in ``storage_dir`` are imported once on first use.
"""

from __future__ import annotations

import json as _json
import logging
import sqlite3
import uuid
from contextlib import closing
from dataclasses import asdict, dataclass, field, fields
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
    summary: str | None = None  # optional post-call AI summary

    def to_dict(self) -> dict:
        d = asdict(self)
        d["started_at"] = self.started_at.isoformat()
        d["ended_at"] = self.ended_at.isoformat() if self.ended_at else None
        d["transcript"] = [e.to_dict() for e in self.transcript]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> CallRecord:
        data = dict(data)
        data["started_at"] = datetime.fromisoformat(data["started_at"])
        data["ended_at"] = (
            datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None
        )
        data["transcript"] = [CallTranscriptEntry.from_dict(e) for e in data.get("transcript", [])]
        # Drop unknown keys so older/newer payloads round-trip safely.
        allowed = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in allowed})

    @staticmethod
    def generate_id() -> str:
        return uuid.uuid4().hex[:12]


class CallManager:
    """Manages call record storage and retrieval (SQLite-backed)."""

    def __init__(self, storage_dir: str = "./data/calls"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_dir / "calls.db"
        self._init_db()
        self._migrate_legacy_json()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS calls ("
                "  id TEXT PRIMARY KEY,"
                "  started_at TEXT NOT NULL,"
                "  payload TEXT NOT NULL"
                ")"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_calls_started_at ON calls(started_at)")

    def _migrate_legacy_json(self) -> None:
        """Import any legacy per-call JSON files once (idempotent)."""
        json_files = [p for p in self.storage_dir.glob("*.json")]
        if not json_files:
            return
        with closing(self._connect()) as conn, conn:
            existing = {row[0] for row in conn.execute("SELECT id FROM calls")}
            imported = 0
            for path in json_files:
                if path.stem in existing:
                    continue
                try:
                    record = CallRecord.from_dict(_json.loads(path.read_text(encoding="utf-8")))
                    conn.execute(
                        "INSERT OR REPLACE INTO calls (id, started_at, payload) VALUES (?, ?, ?)",
                        (
                            record.id,
                            record.started_at.isoformat(),
                            _json.dumps(record.to_dict()),
                        ),
                    )
                    imported += 1
                except Exception as exc:
                    _logger.warning(f"Skipping unmigratable call file {path.name}: {exc}")
            if imported:
                _logger.info(f"Migrated {imported} legacy call record(s) into SQLite")

    def save_call(self, record: CallRecord) -> None:
        """Save (insert or replace) a call record."""
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT OR REPLACE INTO calls (id, started_at, payload) VALUES (?, ?, ?)",
                (record.id, record.started_at.isoformat(), _json.dumps(record.to_dict())),
            )
        _logger.info(f"Saved call record {record.id} ({len(record.transcript)} turns)")

    def get_call(self, call_id: str) -> CallRecord | None:
        """Retrieve a call record by ID."""
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT payload FROM calls WHERE id = ?", (call_id,)).fetchone()
        if row is None:
            return None
        try:
            return CallRecord.from_dict(_json.loads(row["payload"]))
        except Exception as exc:
            _logger.warning(f"Failed to load call {call_id}: {exc}")
            return None

    def list_calls(self, limit: int | None = None, offset: int = 0) -> list[CallRecord]:
        """List call records, most recent first. Pass limit/offset to paginate."""
        sql = "SELECT payload FROM calls ORDER BY started_at DESC"
        params: list = []
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params = [limit, offset]
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        records: list[CallRecord] = []
        for row in rows:
            try:
                records.append(CallRecord.from_dict(_json.loads(row["payload"])))
            except Exception as exc:
                _logger.warning(f"Failed to load a call record: {exc}")
        return records

    def count_calls(self) -> int:
        """Total number of stored call records."""
        with closing(self._connect()) as conn:
            return conn.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
