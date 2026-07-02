"""SIP trunk and dispatch rule configuration helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass

from proximus.config import get_settings


@dataclass
class InboundTrunkConfig:
    """Configuration for a LiveKit inbound SIP trunk."""

    name: str
    phone_numbers: list[str]
    krisp_enabled: bool = True


@dataclass
class OutboundTrunkConfig:
    """Configuration for a LiveKit outbound SIP trunk."""

    name: str
    address: str
    username: str
    password: str


@dataclass
class DispatchRuleConfig:
    """Configuration for a LiveKit SIP dispatch rule."""

    name: str
    room_prefix: str
    agent_name: str
    metadata: dict | None = None


# Telnyx IP ranges for SIP (for trunk allowed_addresses)
# See: https://support.telnyx.com/en/articles/4455513-telnyx-sip-signaling-ip-addresses
TELNYX_SIP_IPS = [
    "54.172.60.0/23",  # US East
    "54.244.51.0/24",  # US West
    "52.215.127.0/24",  # EU
]


# Twilio Elastic SIP Trunking IP ranges (signaling)
# See: https://www.twilio.com/docs/sip-trunking/ip-addresses
TWILIO_SIP_IPS = [
    "54.172.60.0/23",  # Twilio US East
    "54.244.51.0/24",  # Twilio US West
    "54.171.127.192/26",  # Twilio EU (Ireland)
    "35.156.191.128/25",  # Twilio EU (Frankfurt)
    "54.65.63.192/26",  # Twilio AP (Tokyo)
    "54.169.127.128/26",  # Twilio AP (Singapore)
    "54.252.254.64/26",  # Twilio AP (Sydney)
]


def generate_inbound_trunk_command(config: InboundTrunkConfig | None = None) -> str:
    """Generate the livekit-cli command to create an inbound SIP trunk.

    Args:
        config: Optional custom config. If not provided, uses settings.

    Returns:
        The CLI command string.
    """
    settings = get_settings()

    if config is None:
        config = InboundTrunkConfig(
            name="Telnyx Inbound",
            phone_numbers=[settings.telnyx_phone_number],
        )

    numbers_arg = " ".join(f'"{n}"' for n in config.phone_numbers)
    allowed_ips = ",".join(TELNYX_SIP_IPS)

    cmd = f"""livekit-cli sip inbound create \\
  --name "{config.name}" \\
  --numbers {numbers_arg} \\
  --allowed-addresses "{allowed_ips}" \\
  --krisp-enabled {str(config.krisp_enabled).lower()}"""

    return cmd


def generate_outbound_trunk_command(config: OutboundTrunkConfig | None = None) -> str:
    """Generate the livekit-cli command to create an outbound SIP trunk.

    Args:
        config: Optional custom config. If not provided, uses settings.

    Returns:
        The CLI command string.
    """
    settings = get_settings()

    if config is None:
        config = OutboundTrunkConfig(
            name="Telnyx Outbound",
            address="sip.telnyx.com",
            username=settings.telnyx_sip_username,
            password=settings.telnyx_sip_password.get_secret_value(),
        )

    cmd = f"""livekit-cli sip outbound create \\
  --name "{config.name}" \\
  --address "{config.address}" \\
  --username "{config.username}" \\
  --password "{config.password}" \\
  --headers "X-Telnyx-Username:{config.username}" """

    return cmd


def generate_dispatch_rule_command(
    trunk_id: str,
    config: DispatchRuleConfig | None = None,
) -> str:
    """Generate the livekit-cli command to create a dispatch rule.

    Args:
        trunk_id: The ID of the inbound trunk to attach to.
        config: Optional custom config. If not provided, uses settings.

    Returns:
        The CLI command string.
    """
    settings = get_settings()

    if config is None:
        config = DispatchRuleConfig(
            name="PROXIMUS Dispatch",
            room_prefix=settings.room_prefix,
            agent_name=settings.agent_name,
            metadata={"source": "telnyx", "agent": "proximus"},
        )

    # Build the dispatch rule JSON
    rule = {
        "rule": {
            "dispatchRuleIndividual": {
                "roomPrefix": config.room_prefix,
            }
        },
        "name": config.name,
        "trunkIds": [trunk_id],
    }

    # Add room config with agent
    if config.agent_name:
        rule["roomConfig"] = {
            "agents": [{"agentName": config.agent_name}],
        }
        if config.metadata:
            rule["roomConfig"]["metadata"] = json.dumps(config.metadata)

    rule_json = json.dumps(rule, indent=2)

    cmd = f"""livekit-cli sip dispatch create --request '{rule_json}'"""

    return cmd


def generate_twilio_inbound_trunk_command(config: InboundTrunkConfig | None = None) -> str:
    """Generate the livekit-cli command to create a Twilio inbound SIP trunk."""
    settings = get_settings()

    if config is None:
        config = InboundTrunkConfig(
            name="Twilio Inbound",
            phone_numbers=[settings.twilio_phone_number],
        )

    numbers_arg = " ".join(f'"{n}"' for n in config.phone_numbers)
    allowed_ips = ",".join(TWILIO_SIP_IPS)

    cmd = f"""livekit-cli sip inbound create \\
  --name "{config.name}" \\
  --numbers {numbers_arg} \\
  --allowed-addresses "{allowed_ips}" \\
  --krisp-enabled {str(config.krisp_enabled).lower()}"""

    return cmd


def generate_twilio_outbound_trunk_command(config: OutboundTrunkConfig | None = None) -> str:
    """Generate the livekit-cli command to create a Twilio outbound SIP trunk."""
    settings = get_settings()

    if config is None:
        # Twilio Elastic SIP Trunking uses a Credential List for SIP digest auth,
        # NOT the Account SID / Auth Token (those are REST API credentials only).
        # Create a Credential List in Twilio Console:
        # Elastic SIP Trunking -> your trunk -> Authentication -> Credential Lists
        termination_uri = settings.twilio_termination_uri or "<your-trunk>.pstn.twilio.com"
        config = OutboundTrunkConfig(
            name="Twilio Outbound",
            address=termination_uri,
            username=settings.twilio_sip_username,
            password=settings.twilio_sip_password.get_secret_value(),
        )
    cmd = f"""livekit-cli sip outbound create \\
  --name "{config.name}" \\
  --address "{config.address}" \\
  --username "{config.username}" \\
  --password "{config.password}" """

    return cmd


def generate_twilio_setup_instructions() -> str:
    """Generate complete setup instructions for Twilio Elastic SIP Trunking + LiveKit."""
    settings = get_settings()

    twilio_dispatch_cmd = generate_dispatch_rule_command(
        "<TRUNK_ID>",
        DispatchRuleConfig(
            name="PROXIMUS Dispatch",
            room_prefix=settings.room_prefix,
            agent_name=settings.agent_name,
            metadata={"source": "twilio", "agent": "proximus"},
        ),
    )

    instructions = f"""
# PROXIMUS - Twilio Elastic SIP Trunking + LiveKit Setup Instructions

## Prerequisites
- LiveKit Cloud account or self-hosted LiveKit with SIP enabled
- Twilio account with a phone number: {settings.twilio_phone_number or "<not configured>"}
- livekit-cli installed: `brew install livekit-cli` or `go install github.com/livekit/livekit-cli/cmd/livekit-cli@latest`

## Step 1: Configure LiveKit CLI

```bash
livekit-cli project add \\
  --url {settings.livekit_url} \\
  --api-key {settings.livekit_api_key} \\
  --api-secret <your-secret>
```

## Step 2: Configure Twilio Elastic SIP Trunk (Twilio Console)

1. Log in to https://console.twilio.com
2. Navigate to **Voice → Elastic SIP Trunking → Trunks**
3. Click **Create new SIP Trunk**
4. Under **Origination** (inbound), add an Origination URI pointing to your LiveKit SIP URI:
   - URI: `sip:{settings.livekit_sip_uri or "<your-livekit-sip-uri>"}`
   - Priority: 10, Weight: 10
5. Under **Termination** (outbound), note your **Termination SIP URI** — set as `TWILIO_TERMINATION_URI` in `.env`
6. Under **Phone Numbers**, attach your Twilio number: `{settings.twilio_phone_number or "<your-twilio-number>"}`

## Step 3: Create Inbound SIP Trunk (LiveKit side)

```bash
{generate_twilio_inbound_trunk_command()}
```

**Save the trunk ID from the output!**

## Step 4: Create Dispatch Rule

Replace `<TRUNK_ID>` with the ID from Step 3:

```bash
{twilio_dispatch_cmd}
```

## Step 5: Create a Twilio Credential List for outbound auth

Twilio Elastic SIP Trunking uses **digest authentication via a Credential List** for
outbound calls — your Account SID and Auth Token are REST API credentials only and
will not work for SIP digest auth.

1. In the Twilio Console go to **Elastic SIP Trunking → your trunk → Authentication**
2. Under **Credential Lists**, click **Create new Credential List**
3. Add a username and password, then link the list to your trunk
4. Set `TWILIO_SIP_USERNAME` and `TWILIO_SIP_PASSWORD` in `.env` to those values

## Step 6: Create Outbound SIP Trunk (LiveKit side)

```bash
{generate_twilio_outbound_trunk_command()}
```

**Save this trunk ID and set it as `OUTBOUND_TRUNK_ID` in `.env`.**

## Step 7: Start PROXIMUS Agent

Set these in `.env`:
SIP_PROVIDER=twilio

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

TWILIO_AUTH_TOKEN=your-auth-token

TWILIO_PHONE_NUMBER=+1234567890

TWILIO_TERMINATION_URI=your-trunk.pstn.twilio.com
TWILIO_SIP_USERNAME=your-credential-list-username
TWILIO_SIP_PASSWORD=your-credential-list-password
"""
    return instructions


def generate_setup_instructions(provider: str | None = None) -> str:
    """Generate complete setup instructions for the chosen SIP provider + LiveKit.

    Args:
        provider: "telnyx" or "twilio". Defaults to the value of SIP_PROVIDER in settings.

    Returns:
        Formatted instructions string.
    """
    settings = get_settings()
    resolved_provider = provider or settings.sip_provider

    if resolved_provider == "twilio":
        return generate_twilio_setup_instructions()

    instructions = f"""
# PROXIMUS - Telnyx + LiveKit Setup Instructions
 
## Prerequisites
- LiveKit Cloud account or self-hosted LiveKit with SIP enabled
- Telnyx account with phone number: {settings.telnyx_phone_number or "<not configured>"}
- livekit-cli installed: `brew install livekit-cli` or `go install github.com/livekit/livekit-cli/cmd/livekit-cli@latest`
 
## Step 1: Configure LiveKit CLI
 
```bash
livekit-cli project add \\
  --url {settings.livekit_url} \\
  --api-key {settings.livekit_api_key} \\
  --api-secret <your-secret>
```
 
## Step 2: Create Inbound SIP Trunk
 
This trunk receives calls from Telnyx:
 
```bash
{generate_inbound_trunk_command()}
```
 
**Save the trunk ID from the output!**
 
## Step 3: Create Dispatch Rule
 
Replace `<TRUNK_ID>` with the ID from Step 2:
 
```bash
{generate_dispatch_rule_command("<TRUNK_ID>")}
```
 
## Step 4: Configure Telnyx (in Mission Control Portal)
 
1. Go to Real-Time Communications → Voice → SIP Trunking
2. Create new FQDN connection:
   - FQDN: `{settings.telnyx_sip_uri or "<your-livekit-sip-uri>"}`
   - Port: 5060
   - Transport: TCP (recommended)
 
3. Configure Authentication:
   - Method: Credentials
   - Username: `{settings.telnyx_sip_username or "<your-username>"}`
   - Password: (your password)
 
4. Link your phone number to this SIP connection
 
## Step 5: Start PROXIMUS Agent
 
```bash
python -m proximus agent
```
 
## Step 6: Test
 
Call your Telnyx number. The call should:
1. Route through Telnyx to LiveKit
2. Create a new room with prefix `{settings.room_prefix}`
3. Connect to your PROXIMUS agent
"""
    return instructions
