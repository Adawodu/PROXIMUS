"""CLI commands for PROXIMUS setup and configuration."""

from __future__ import annotations

import argparse
import sys

from proximus.config import get_settings
from proximus.sip.config import (
    generate_dispatch_rule_command,
    generate_inbound_trunk_command,
    generate_outbound_trunk_command,
    generate_setup_instructions,
    generate_twilio_inbound_trunk_command,
    generate_twilio_outbound_trunk_command,
)


def _resolve_provider(args: argparse.Namespace) -> str:
    """Return the SIP provider from --provider flag or settings."""
    if getattr(args, "provider", None):
        return args.provider
    return get_settings().sip_provider


def cmd_setup(args: argparse.Namespace) -> int:
    """Print complete setup instructions."""
    print(generate_setup_instructions(provider=_resolve_provider(args)))
    return 0


def cmd_trunk_inbound(args: argparse.Namespace) -> int:
    """Generate the inbound trunk creation command."""
    provider = _resolve_provider(args)
    if provider == "twilio":
        print("# Create inbound SIP trunk for Twilio Elastic SIP Trunking")
        print(generate_twilio_inbound_trunk_command())
    else:
        print("# Create inbound SIP trunk for Telnyx")
        print(generate_inbound_trunk_command())
    print()
    print("# After running, save the trunk ID for the dispatch rule")
    return 0


def cmd_trunk_outbound(args: argparse.Namespace) -> int:
    """Generate the outbound trunk creation command."""
    provider = _resolve_provider(args)
    if provider == "twilio":
        print("# Create outbound SIP trunk for Twilio Elastic SIP Trunking")
        print(generate_twilio_outbound_trunk_command())
    else:
        print("# Create outbound SIP trunk for Telnyx (for making calls)")
        print(generate_outbound_trunk_command())
    return 0


def cmd_dispatch_rule(args: argparse.Namespace) -> int:
    """Generate the dispatch rule creation command."""
    if not args.trunk_id:
        print("Error: --trunk-id is required", file=sys.stderr)
        print("Run 'proximus sip trunk-inbound' first to get the trunk ID", file=sys.stderr)
        return 1

    print("# Create dispatch rule to route calls to PROXIMUS agent")
    print(generate_dispatch_rule_command(args.trunk_id))
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Show current configuration (without secrets)."""
    settings = get_settings()

    print("PROXIMUS Configuration")
    print("=" * 50)
    print()
    print("LiveKit:")
    print(f"  URL: {settings.livekit_url}")
    print(f"  API Key: {settings.livekit_api_key or '(not set)'}")
    print(
        f"  API Secret: {'*' * 8 if settings.livekit_api_secret.get_secret_value() else '(not set)'}"
    )
    print()
    print(f"SIP Provider: {settings.sip_provider}")
    print()
    print("Telnyx:")
    print(f"  API Key: {'*' * 8 if settings.telnyx_api_key.get_secret_value() else '(not set)'}")
    print(f"  SIP URI: {settings.telnyx_sip_uri or '(not set)'}")
    print(f"  SIP Username: {settings.telnyx_sip_username or '(not set)'}")
    print(
        f"  SIP Password: {'*' * 8 if settings.telnyx_sip_password.get_secret_value() else '(not set)'}"
    )
    print(f"  Phone Number: {settings.telnyx_phone_number or '(not set)'}")
    print()
    print("Twilio:")
    print(f"  Account SID: {settings.twilio_account_sid or '(not set)'}")
    print(
        f"  Auth Token: {'*' * 8 if settings.twilio_auth_token.get_secret_value() else '(not set)'}"
    )
    print(f"  Phone Number: {settings.twilio_phone_number or '(not set)'}")
    print(f"  Termination URI: {settings.twilio_termination_uri or '(not set)'}")
    print(f"  SIP Username (Credential List): {settings.twilio_sip_username or '(not set)'}")
    print(
        f"  SIP Password (Credential List): {'*' * 8 if settings.twilio_sip_password.get_secret_value() else '(not set)'}"
    )
    print()
    print("Agent:")
    print(f"  Name: {settings.agent_name}")
    print(f"  Room Prefix: {settings.room_prefix}")
    print()
    print("AI Provider:")
    print(f"  Provider: {settings.ai_provider}")
    print(
        f"  Anthropic Key: {'*' * 8 if settings.anthropic_api_key.get_secret_value() else '(not set)'}"
    )
    print(f"  OpenAI Key: {'*' * 8 if settings.openai_api_key.get_secret_value() else '(not set)'}")
    print()
    print("Speech Services:")
    print(
        f"  Deepgram Key: {'*' * 8 if settings.deepgram_api_key.get_secret_value() else '(not set)'}"
    )
    print(
        f"  Cartesia Key: {'*' * 8 if settings.cartesia_api_key.get_secret_value() else '(not set)'}"
    )

    return 0


def run_cli() -> int:
    """Run the SIP CLI with subcommands."""
    parser = argparse.ArgumentParser(
        prog="proximus sip",
        description="PROXIMUS SIP configuration commands (Telnyx or Twilio)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")

    _provider_kwargs = dict(
        choices=["telnyx", "twilio"],
        default=None,
        help="SIP provider to use (overrides SIP_PROVIDER env var)",
    )

    # setup
    setup_parser = subparsers.add_parser("setup", help="Print complete setup instructions")
    setup_parser.add_argument("--provider", **_provider_kwargs)
    setup_parser.set_defaults(func=cmd_setup)

    # trunk-inbound
    inbound_parser = subparsers.add_parser(
        "trunk-inbound", help="Generate inbound trunk CLI command"
    )
    inbound_parser.add_argument("--provider", **_provider_kwargs)
    inbound_parser.set_defaults(func=cmd_trunk_inbound)

    # trunk-outbound
    outbound_parser = subparsers.add_parser(
        "trunk-outbound", help="Generate outbound trunk CLI command"
    )
    outbound_parser.add_argument("--provider", **_provider_kwargs)
    outbound_parser.set_defaults(func=cmd_trunk_outbound)

    # dispatch-rule
    dispatch_parser = subparsers.add_parser(
        "dispatch-rule", help="Generate dispatch rule CLI command"
    )
    dispatch_parser.add_argument(
        "--trunk-id",
        required=True,
        help="The inbound trunk ID to attach the dispatch rule to",
    )
    dispatch_parser.set_defaults(func=cmd_dispatch_rule)

    # config
    config_parser = subparsers.add_parser("config", help="Show current configuration")
    config_parser.set_defaults(func=cmd_config)

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        return 1

    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(run_cli())