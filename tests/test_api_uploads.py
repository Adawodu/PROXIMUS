"""Tests for resume upload validation (type + size guards).

Both cases are rejected before any parsing or storage write, so these tests
do not touch ./data/resumes.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from proximus.api.main import MAX_UPLOAD_BYTES, app
from proximus.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_unsupported_type_rejected(client):
    resp = client.post(
        "/resumes",
        files={"file": ("resume.exe", b"data", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


def test_oversized_upload_rejected(client):
    oversized = b"a" * (MAX_UPLOAD_BYTES + 1024)
    resp = client.post(
        "/resumes",
        files={"file": ("big.txt", oversized, "text/plain")},
    )
    assert resp.status_code == 413
    assert "too large" in resp.json()["detail"]
