"""Tests for the Twilio SIP backend (no API keys required)."""

from __future__ import annotations

import pytest

from proximus.config import Settings, get_settings
from proximus.sip.config import (
    TWILIO_SIP_IPS,
    OutboundTrunkConfig,
    generate_setup_instructions,
    generate_twilio_inbound_trunk_command,
    generate_twilio_outbound_trunk_command,
    generate_twilio_setup_instructions,
)


def _settings(**kwargs) -> Settings:
    return Settings(_env_file=None, **kwargs)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Reset the lru_cache around every test so monkeypatch.setenv takes effect."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Config / Settings
# ---------------------------------------------------------------------------

def test_sip_provider_default_is_telnyx():
    s = _settings()
    assert s.sip_provider == "telnyx"


def test_sip_provider_can_be_set_to_twilio():
    s = _settings(sip_provider="twilio")
    assert s.sip_provider == "twilio"


def test_twilio_fields_default_to_empty():
    s = _settings()
    assert s.twilio_account_sid == ""
    assert s.twilio_phone_number == ""
    assert s.twilio_termination_uri == ""
    assert s.twilio_sip_username == ""
    assert s.twilio_auth_token.get_secret_value() == ""
    assert s.twilio_sip_password.get_secret_value() == ""


def test_twilio_fields_loaded_from_env():
    s = _settings(
        twilio_account_sid="ACtest",
        twilio_phone_number="+15550001234",
        twilio_termination_uri="mytesttrunk.pstn.twilio.com",
        twilio_sip_username="cred-list-user",
    )
    assert s.twilio_account_sid == "ACtest"
    assert s.twilio_phone_number == "+15550001234"
    assert s.twilio_termination_uri == "mytesttrunk.pstn.twilio.com"
    assert s.twilio_sip_username == "cred-list-user"


# ---------------------------------------------------------------------------
# SIP IP list
# ---------------------------------------------------------------------------

def test_twilio_sip_ips_is_non_empty():
    assert len(TWILIO_SIP_IPS) > 0


def test_twilio_sip_ips_are_cidr_strings():
    for cidr in TWILIO_SIP_IPS:
        assert "/" in cidr, f"Expected CIDR notation, got: {cidr}"


# ---------------------------------------------------------------------------
# Inbound trunk command
# ---------------------------------------------------------------------------

def test_twilio_inbound_trunk_command_contains_twilio_ips(monkeypatch):
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+15559876543")
    cmd = generate_twilio_inbound_trunk_command()
    for ip in TWILIO_SIP_IPS:
        assert ip in cmd


def test_twilio_inbound_trunk_command_contains_phone_number(monkeypatch):
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+15559876543")
    cmd = generate_twilio_inbound_trunk_command()
    assert "+15559876543" in cmd


def test_twilio_inbound_trunk_command_has_livekit_cli_prefix():
    cmd = generate_twilio_inbound_trunk_command()
    assert cmd.strip().startswith("livekit-cli sip inbound create")


# ---------------------------------------------------------------------------
# Outbound trunk command — uses Credential List creds, NOT Account SID/Auth Token
# ---------------------------------------------------------------------------

def test_twilio_outbound_trunk_uses_credential_list_not_account_sid(monkeypatch):
    """Twilio SIP digest auth requires a Credential List, not Account SID/Auth Token."""
    monkeypatch.setenv("TWILIO_SIP_USERNAME", "cred-list-user")
    monkeypatch.setenv("TWILIO_SIP_PASSWORD", "cred-list-pass")
    monkeypatch.setenv("TWILIO_TERMINATION_URI", "mytrunk.pstn.twilio.com")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACshouldnotappear")
    cmd = generate_twilio_outbound_trunk_command()
    assert "cred-list-user" in cmd
    assert "cred-list-pass" in cmd
    assert "ACshouldnotappear" not in cmd


def test_twilio_outbound_trunk_command_uses_termination_uri():
    """Config-driven test: bypass get_settings() entirely."""
    config = OutboundTrunkConfig(
        name="Twilio Outbound",
        address="mytesttrunk.pstn.twilio.com",
        username="cred-user",
        password="cred-pass",
    )
    cmd = generate_twilio_outbound_trunk_command(config=config)
    assert "mytesttrunk.pstn.twilio.com" in cmd
    assert "cred-user" in cmd


def test_twilio_outbound_trunk_command_has_livekit_cli_prefix():
    cmd = generate_twilio_outbound_trunk_command()
    assert cmd.strip().startswith("livekit-cli sip outbound create")


# ---------------------------------------------------------------------------
# Setup instructions
# ---------------------------------------------------------------------------

def test_twilio_setup_instructions_mentions_twilio():
    instructions = generate_twilio_setup_instructions()
    assert "Twilio" in instructions
    assert "Elastic SIP Trunking" in instructions


def test_twilio_setup_instructions_mentions_livekit():
    instructions = generate_twilio_setup_instructions()
    assert "LiveKit" in instructions


def test_twilio_setup_instructions_mentions_credential_list():
    """Instructions must guide users to create a Credential List, not use Account SID."""
    instructions = generate_twilio_setup_instructions()
    assert "Credential List" in instructions


def test_generate_setup_instructions_routes_to_twilio():
    instructions = generate_setup_instructions(provider="twilio")
    assert "Twilio" in instructions
    assert "Telnyx" not in instructions


def test_generate_setup_instructions_routes_to_telnyx():
    instructions = generate_setup_instructions(provider="telnyx")
    assert "Telnyx" in instructions
    assert "Twilio Elastic SIP Trunking" not in instructions


def test_generate_setup_instructions_default_is_telnyx():
    instructions = generate_setup_instructions()
    assert "Telnyx" in instructions