"""Resume parsing and context management (SQLite-backed).

Resume metadata and phone links live in a SQLite database
(``<storage_dir>/resumes.db``); the uploaded resume files themselves stay in
``storage_dir``. A legacy ``registry.json`` is imported once on first use.
"""

from __future__ import annotations

import hashlib
import json as _json
import logging
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from pathlib import Path

import pdfplumber
from docx import Document

_logger = logging.getLogger(__name__)


@dataclass
class Resume:
    """Parsed resume with metadata."""

    id: str
    candidate_name: str
    content: str
    file_path: str
    created_at: datetime = field(default_factory=datetime.now)
    voice: str = ""  # optional per-resume TTS voice id (empty -> provider default)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Resume:
        data = dict(data)
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        allowed = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in allowed})

    def to_system_prompt(self) -> str:
        """Generate a system prompt incorporating the resume context."""
        return f"""You are PROXIMUS, an AI screening assistant speaking on behalf of {self.candidate_name} during a recruiter screening call.

You are on a phone call with a recruiter conducting a screening interview. Your role is to answer their questions naturally and professionally using the resume information below. Represent the candidate accurately and truthfully.

Guidelines:
- Answer in the first person on the candidate's behalf ("I have 5 years of experience...")
- Be concise - this is a phone call, not a written response
- Only state facts supported by the resume; never invent experience, skills, or credentials
- If asked something not covered by the resume, say you'd need to follow up rather than guessing
- If asked, be honest that you are an AI assistant helping handle the call
- Sound natural and confident, not robotic

CANDIDATE RESUME:
{self.content}
"""


class ResumeManager:
    """Manages resume storage and retrieval (SQLite-backed)."""

    _LEGACY_REGISTRY_FILE = "registry.json"

    def __init__(self, storage_dir: str = "./data/resumes"):
        """Initialize the resume manager.

        Args:
            storage_dir: Directory for storing resume files and the database.
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_dir / "resumes.db"
        self._init_db()
        self._migrate_legacy_registry()

    # ---- persistence ----

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS resumes ("
                "  id TEXT PRIMARY KEY,"
                "  created_at TEXT NOT NULL,"
                "  payload TEXT NOT NULL"
                ")"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS phone_links ("
                "  phone TEXT PRIMARY KEY,"
                "  resume_id TEXT NOT NULL"
                ")"
            )

    def _migrate_legacy_registry(self) -> None:
        """Import a legacy registry.json once (idempotent — skips if DB has data)."""
        path = self.storage_dir / self._LEGACY_REGISTRY_FILE
        if not path.exists():
            return
        with closing(self._connect()) as conn, conn:
            has_rows = conn.execute("SELECT 1 FROM resumes LIMIT 1").fetchone()
            if has_rows:
                return
            try:
                data = _json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                _logger.warning(f"Failed to read legacy registry: {exc}")
                return
            n_res = 0
            for rid, rd in data.get("resumes", {}).items():
                try:
                    resume = Resume.from_dict(rd)
                    conn.execute(
                        "INSERT OR REPLACE INTO resumes (id, created_at, payload) VALUES (?, ?, ?)",
                        (resume.id, resume.created_at.isoformat(), _json.dumps(resume.to_dict())),
                    )
                    n_res += 1
                except Exception as exc:
                    _logger.warning(f"Skipping unmigratable resume {rid}: {exc}")
            for phone, rid in data.get("phone_links", {}).items():
                conn.execute(
                    "INSERT OR REPLACE INTO phone_links (phone, resume_id) VALUES (?, ?)",
                    (phone, rid),
                )
            _logger.info(f"Migrated {n_res} resume(s) and phone links from registry.json")

    def _load_registry(self) -> None:
        """No-op: reads always hit SQLite, so in-memory state can't go stale.

        Retained because the agent calls it to "reload from disk" before a call.
        """
        return

    def _save_resume(self, resume: Resume) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT OR REPLACE INTO resumes (id, created_at, payload) VALUES (?, ?, ?)",
                (resume.id, resume.created_at.isoformat(), _json.dumps(resume.to_dict())),
            )

    # ---- helpers ----

    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for a resume."""
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text content from a PDF file."""
        text_parts: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    def _extract_text_from_docx(self, file_path: Path) -> str:
        """Extract text content from a DOCX file."""
        doc = Document(file_path)
        return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())

    def _extract_candidate_name(self, content: str) -> str:
        """Extract candidate name from resume content.

        Simple heuristic: first non-empty line is usually the name.
        """
        lines = content.strip().split("\n")
        for line in lines:
            cleaned = line.strip()
            if cleaned and len(cleaned) < 100:  # Names aren't usually that long
                return cleaned
        return "Candidate"

    def parse_resume(self, file_path: str | Path, candidate_name: str | None = None) -> Resume:
        """Parse a resume file and store it.

        Args:
            file_path: Path to the resume file (PDF, DOCX, or TXT).
            candidate_name: Optional override for candidate name.

        Returns:
            Parsed Resume object.

        Raises:
            ValueError: If file type is not supported.
            FileNotFoundError: If the file does not exist.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            content = self._extract_text_from_pdf(path)
        elif suffix == ".docx":
            content = self._extract_text_from_docx(path)
        elif suffix == ".txt":
            content = path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        if not candidate_name:
            candidate_name = self._extract_candidate_name(content)

        resume_id = self._generate_id(content)

        resume = Resume(
            id=resume_id,
            candidate_name=candidate_name,
            content=content,
            file_path=str(path.absolute()),
        )

        self._save_resume(resume)
        return resume

    def get_resume(self, resume_id: str) -> Resume | None:
        """Retrieve a resume by ID."""
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT payload FROM resumes WHERE id = ?", (resume_id,)).fetchone()
        if row is None:
            return None
        try:
            return Resume.from_dict(_json.loads(row["payload"]))
        except Exception as exc:
            _logger.warning(f"Failed to load resume {resume_id}: {exc}")
            return None

    def list_resumes(self, limit: int | None = None, offset: int = 0) -> list[Resume]:
        """List stored resumes, most recent first. Pass limit/offset to paginate."""
        sql = "SELECT payload FROM resumes ORDER BY created_at DESC"
        params: list = []
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params = [limit, offset]
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        resumes: list[Resume] = []
        for row in rows:
            try:
                resumes.append(Resume.from_dict(_json.loads(row["payload"])))
            except Exception as exc:
                _logger.warning(f"Failed to load a resume: {exc}")
        return resumes

    def count_resumes(self) -> int:
        """Total number of stored resumes."""
        with closing(self._connect()) as conn:
            return conn.execute("SELECT COUNT(*) FROM resumes").fetchone()[0]

    def set_voice(self, resume_id: str, voice: str) -> Resume | None:
        """Set the per-resume TTS voice id. Returns the updated Resume, or None."""
        resume = self.get_resume(resume_id)
        if resume is None:
            return None
        resume.voice = voice
        self._save_resume(resume)
        return resume

    def delete_resume(self, resume_id: str) -> bool:
        """Delete a resume by ID (cascades to its phone links)."""
        with closing(self._connect()) as conn, conn:
            cur = conn.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
            conn.execute("DELETE FROM phone_links WHERE resume_id = ?", (resume_id,))
            return cur.rowcount > 0

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize a phone number to E.164 format.

        Args:
            phone: Phone number in any format.

        Returns:
            Normalized phone number (digits only, with leading +).
        """
        # Remove all non-digit characters except leading +
        digits = "".join(c for c in phone if c.isdigit())
        # Assume US number if no country code and 10 digits
        if not phone.startswith("+") and len(digits) == 10:
            digits = "1" + digits
        return "+" + digits

    def link_phone(self, phone: str, resume_id: str) -> bool:
        """Link a phone number to a resume.

        Raises:
            ValueError: If resume_id doesn't exist.
        """
        if self.get_resume(resume_id) is None:
            raise ValueError(f"Resume not found: {resume_id}")

        normalized = self.normalize_phone(phone)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT OR REPLACE INTO phone_links (phone, resume_id) VALUES (?, ?)",
                (normalized, resume_id),
            )
        return True

    def unlink_phone(self, phone: str) -> bool:
        """Unlink a phone number from its resume. Returns True if it existed."""
        normalized = self.normalize_phone(phone)
        with closing(self._connect()) as conn, conn:
            cur = conn.execute("DELETE FROM phone_links WHERE phone = ?", (normalized,))
            return cur.rowcount > 0

    def get_resume_by_phone(self, phone: str) -> Resume | None:
        """Get a resume by phone number."""
        normalized = self.normalize_phone(phone)
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT resume_id FROM phone_links WHERE phone = ?", (normalized,)
            ).fetchone()
        if row is None:
            return None
        return self.get_resume(row["resume_id"])

    def list_phone_links(self) -> dict[str, str]:
        """List all phone number to resume mappings."""
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT phone, resume_id FROM phone_links").fetchall()
        return {row["phone"]: row["resume_id"] for row in rows}

    def get_phones_for_resume(self, resume_id: str) -> list[str]:
        """Get all phone numbers linked to a resume."""
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT phone FROM phone_links WHERE resume_id = ?", (resume_id,)
            ).fetchall()
        return [row["phone"] for row in rows]
