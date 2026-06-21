"""Tests for configuration loading (no API keys required)."""

from __future__ import annotations

from pydantic import SecretStr

from proximus.config import Settings


def test_defaults_are_safe_when_env_missing():
    # extra env vars are ignored; defaults should not raise
    settings = Settings(_env_file=None)
    assert settings.ai_provider == "anthropic"
    assert settings.api_port == 8000
    assert settings.agent_name == "proximus-agent"
    assert settings.telnyx_credential_connection_id == ""


def test_secrets_are_wrapped():
    settings = Settings(_env_file=None, anthropic_api_key="secret-value")
    assert isinstance(settings.anthropic_api_key, SecretStr)
    # secret value is not exposed in repr
    assert "secret-value" not in repr(settings.anthropic_api_key)
    assert settings.anthropic_api_key.get_secret_value() == "secret-value"


def test_ai_provider_accepts_openai():
    settings = Settings(_env_file=None, ai_provider="openai")
    assert settings.ai_provider == "openai"
