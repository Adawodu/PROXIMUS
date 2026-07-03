"""Resume parsing and context management."""

from __future__ import annotations

import hashlib
import json as _json
import logging
from dataclasses import asdict, dataclass, field
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

    def to_dict(self) -> dict:
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Resume:
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

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
    """Manages resume storage and retrieval."""

    _REGISTRY_FILE = "registry.json"

    def __init__(self, storage_dir: str = "./data/resumes"):
        """Initialize the resume manager.

        Args:
            storage_dir: Directory for storing resume data.
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._resumes: dict[str, Resume] = {}
        self._phone_to_resume: dict[str, str] = {}  # phone_number -> resume_id
        self._load_registry()

    # ---- persistence ----

    def _registry_path(self) -> Path:
        return self.storage_dir / self._REGISTRY_FILE

    def _save_registry(self) -> None:
        data = {
            "resumes": {rid: r.to_dict() for rid, r in self._resumes.items()},
            "phone_links": dict(self._phone_to_resume),
        }
        self._registry_path().write_text(_json.dumps(data, indent=2), encoding="utf-8")

    def _load_registry(self) -> None:
        path = self._registry_path()
        if not path.exists():
            return
        try:
            data = _json.loads(path.read_text(encoding="utf-8"))
            # Rebuild from disk rather than merging into the current dicts, so
            # resumes/links removed elsewhere (e.g. via the API) don't linger in
            # this process's in-memory state after a reload.
            self._resumes = {
                rid: Resume.from_dict(rd) for rid, rd in data.get("resumes", {}).items()
            }
            self._phone_to_resume = dict(data.get("phone_links", {}))
            _logger.info(
                f"Loaded {len(self._resumes)} resumes, {len(self._phone_to_resume)} phone links from registry"
            )
        except Exception as exc:
            _logger.warning(f"Failed to load registry: {exc}")

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
            file_path: Path to the resume file (PDF or DOCX).
            candidate_name: Optional override for candidate name.

        Returns:
            Parsed Resume object.

        Raises:
            ValueError: If file type is not supported.
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

        self._resumes[resume_id] = resume
        self._save_registry()
        return resume

    def get_resume(self, resume_id: str) -> Resume | None:
        """Retrieve a resume by ID."""
        return self._resumes.get(resume_id)

    def list_resumes(self) -> list[Resume]:
        """List all stored resumes."""
        return list(self._resumes.values())

    def delete_resume(self, resume_id: str) -> bool:
        """Delete a resume by ID."""
        if resume_id in self._resumes:
            del self._resumes[resume_id]
            # Also remove any phone links to this resume
            phones_to_remove = [
                phone for phone, rid in self._phone_to_resume.items() if rid == resume_id
            ]
            for phone in phones_to_remove:
                del self._phone_to_resume[phone]
            self._save_registry()
            return True
        return False

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

        Args:
            phone: Phone number (will be normalized).
            resume_id: Resume ID to link to.

        Returns:
            True if linked successfully.

        Raises:
            ValueError: If resume_id doesn't exist.
        """
        if resume_id not in self._resumes:
            raise ValueError(f"Resume not found: {resume_id}")

        normalized = self.normalize_phone(phone)
        self._phone_to_resume[normalized] = resume_id
        self._save_registry()
        return True

    def unlink_phone(self, phone: str) -> bool:
        """Unlink a phone number from its resume.

        Args:
            phone: Phone number to unlink.

        Returns:
            True if unlinked, False if not found.
        """
        normalized = self.normalize_phone(phone)
        if normalized in self._phone_to_resume:
            del self._phone_to_resume[normalized]
            self._save_registry()
            return True
        return False

    def get_resume_by_phone(self, phone: str) -> Resume | None:
        """Get a resume by phone number.

        Args:
            phone: Phone number to look up.

        Returns:
            Resume if found, None otherwise.
        """
        normalized = self.normalize_phone(phone)
        resume_id = self._phone_to_resume.get(normalized)
        if resume_id:
            return self._resumes.get(resume_id)
        return None

    def list_phone_links(self) -> dict[str, str]:
        """List all phone number to resume mappings.

        Returns:
            Dict of phone_number -> resume_id.
        """
        return dict(self._phone_to_resume)

    def get_phones_for_resume(self, resume_id: str) -> list[str]:
        """Get all phone numbers linked to a resume.

        Args:
            resume_id: Resume ID to look up.

        Returns:
            List of phone numbers linked to this resume.
        """
        return [phone for phone, rid in self._phone_to_resume.items() if rid == resume_id]
