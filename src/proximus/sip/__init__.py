"""SIP configuration and Telnyx integration."""

from proximus.sip.config import (
    generate_dispatch_rule_command,
    generate_inbound_trunk_command,
    generate_outbound_trunk_command,
)

__all__ = [
    "generate_inbound_trunk_command",
    "generate_outbound_trunk_command",
    "generate_dispatch_rule_command",
]
