"""Tests for resume parsing and phone-link management (no API keys required)."""

from __future__ import annotations

import pytest

from proximus.context.resume import Resume, ResumeManager

SAMPLE_RESUME = """Jane Doe
Senior Software Engineer

Experience:
- 6 years building backend systems in Python
- Led a team of 4 engineers
Skills: Python, FastAPI, PostgreSQL
"""


@pytest.fixture
def manager(tmp_path):
    return ResumeManager(storage_dir=str(tmp_path / "resumes"))


@pytest.fixture
def sample_resume(tmp_path):
    path = tmp_path / "jane.txt"
    path.write_text(SAMPLE_RESUME, encoding="utf-8")
    return path


class TestNormalizePhone:
    def test_adds_plus_and_us_country_code_for_10_digits(self):
        assert ResumeManager.normalize_phone("(415) 555-0100") == "+14155550100"

    def test_keeps_existing_country_code(self):
        assert ResumeManager.normalize_phone("+44 20 7946 0958") == "+442079460958"

    def test_strips_formatting(self):
        assert ResumeManager.normalize_phone("1-415-555-0100") == "+14155550100"

    def test_idempotent(self):
        once = ResumeManager.normalize_phone("4155550100")
        assert ResumeManager.normalize_phone(once) == once


class TestParseResume:
    def test_parses_txt_and_extracts_name(self, manager, sample_resume):
        resume = manager.parse_resume(sample_resume)
        assert resume.candidate_name == "Jane Doe"
        assert "FastAPI" in resume.content
        assert resume.id

    def test_candidate_name_override(self, manager, sample_resume):
        resume = manager.parse_resume(sample_resume, candidate_name="J. Doe")
        assert resume.candidate_name == "J. Doe"

    def test_id_is_deterministic_for_same_content(self, manager, sample_resume):
        first = manager.parse_resume(sample_resume)
        second = manager.parse_resume(sample_resume)
        assert first.id == second.id

    def test_unsupported_file_type_raises(self, manager, tmp_path):
        bad = tmp_path / "resume.rtf"
        bad.write_text("nope", encoding="utf-8")
        with pytest.raises(ValueError):
            manager.parse_resume(bad)

    def test_missing_file_raises(self, manager, tmp_path):
        with pytest.raises(FileNotFoundError):
            manager.parse_resume(tmp_path / "does-not-exist.txt")


class TestPhoneLinks:
    def test_link_and_lookup_by_phone(self, manager, sample_resume):
        resume = manager.parse_resume(sample_resume)
        manager.link_phone("(415) 555-0100", resume.id)
        found = manager.get_resume_by_phone("4155550100")
        assert found is not None
        assert found.id == resume.id

    def test_link_unknown_resume_raises(self, manager):
        with pytest.raises(ValueError):
            manager.link_phone("4155550100", "nonexistent")

    def test_unlink(self, manager, sample_resume):
        resume = manager.parse_resume(sample_resume)
        manager.link_phone("4155550100", resume.id)
        assert manager.unlink_phone("4155550100") is True
        assert manager.get_resume_by_phone("4155550100") is None

    def test_unlink_missing_returns_false(self, manager):
        assert manager.unlink_phone("4155550100") is False

    def test_delete_resume_cascades_to_phone_links(self, manager, sample_resume):
        resume = manager.parse_resume(sample_resume)
        manager.link_phone("4155550100", resume.id)
        assert manager.delete_resume(resume.id) is True
        assert manager.get_resume_by_phone("4155550100") is None
        assert manager.get_resume(resume.id) is None


class TestPersistence:
    def test_registry_survives_reload(self, tmp_path, sample_resume):
        storage = str(tmp_path / "resumes")
        m1 = ResumeManager(storage_dir=storage)
        resume = m1.parse_resume(sample_resume)
        m1.link_phone("4155550100", resume.id)

        m2 = ResumeManager(storage_dir=storage)
        assert m2.get_resume(resume.id) is not None
        assert m2.get_resume_by_phone("4155550100") is not None


class TestSystemPrompt:
    def test_prompt_includes_name_and_content_and_honesty(self):
        resume = Resume(
            id="abc",
            candidate_name="Jane Doe",
            content="Python expert",
            file_path="/tmp/x.txt",
        )
        prompt = resume.to_system_prompt()
        assert "Jane Doe" in prompt
        assert "Python expert" in prompt
        # Honesty guardrails must be present
        assert "never invent" in prompt.lower()
