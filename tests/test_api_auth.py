"""Tests for the API-key authentication dependency (no external services)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from proximus.api.main import app
from proximus.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Reset the lru_cache so monkeypatch.setenv("API_KEY", ...) takes effect."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _set_key(monkeypatch, value: str) -> None:
    monkeypatch.setenv("API_KEY", value)
    get_settings.cache_clear()


# --- /health is always public --------------------------------------------------


def test_health_public_without_key(client):
    assert client.get("/health").status_code == 200


def test_health_public_even_when_key_set(monkeypatch, client):
    _set_key(monkeypatch, "secret-key")
    assert client.get("/health").status_code == 200


# --- Protected routes ----------------------------------------------------------


def test_protected_open_when_no_key_configured(client):
    # No API_KEY configured -> unauthenticated dev mode.
    assert client.get("/resumes").status_code == 200


def test_protected_requires_key_when_configured(monkeypatch, client):
    _set_key(monkeypatch, "secret-key")
    assert client.get("/resumes").status_code == 401


def test_protected_rejects_wrong_key(monkeypatch, client):
    _set_key(monkeypatch, "secret-key")
    assert client.get("/resumes", headers={"X-API-Key": "wrong"}).status_code == 401


def test_protected_accepts_correct_key(monkeypatch, client):
    _set_key(monkeypatch, "secret-key")
    assert client.get("/resumes", headers={"X-API-Key": "secret-key"}).status_code == 200
