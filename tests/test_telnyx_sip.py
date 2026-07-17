"""Tests for the Telnyx SIP signaling IP config (no API keys required)."""

from __future__ import annotations

import ipaddress

from proximus.sip.config import (
    TELNYX_SIP_IPS,
    generate_inbound_trunk_command,
)

# Old, incorrect ranges that used to live in TELNYX_SIP_IPS — these are actually
# AWS/Twilio ranges and must never come back (they'd break inbound allow-listing).
_WRONG_LEGACY_RANGES = {"54.172.60.0/23", "54.244.51.0/24", "52.215.127.0/24"}


def test_telnyx_sip_ips_is_non_empty():
    assert len(TELNYX_SIP_IPS) > 0


def test_telnyx_sip_ips_are_valid_cidrs():
    for cidr in TELNYX_SIP_IPS:
        # Raises ValueError if not a valid network in strict (host-bits-zero) form.
        ipaddress.ip_network(cidr, strict=True)


def test_telnyx_sip_ips_are_real_telnyx_signaling_ranges():
    # Regression guard: the wrong AWS/Twilio ranges must not reappear, and the
    # authoritative Telnyx US signaling IPs must be covered.
    assert _WRONG_LEGACY_RANGES.isdisjoint(TELNYX_SIP_IPS)
    us_signaling = [ipaddress.ip_address("192.76.120.10"), ipaddress.ip_address("64.16.250.10")]
    nets = [ipaddress.ip_network(c) for c in TELNYX_SIP_IPS]
    for ip in us_signaling:
        assert any(ip in n for n in nets), f"US signaling IP {ip} not covered by TELNYX_SIP_IPS"


def test_inbound_trunk_command_contains_telnyx_ips(monkeypatch):
    monkeypatch.setenv("TELNYX_PHONE_NUMBER", "+12407718989")
    cmd = generate_inbound_trunk_command()
    for ip in TELNYX_SIP_IPS:
        assert ip in cmd
