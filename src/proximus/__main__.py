"""Main entry point for PROXIMUS."""

from __future__ import annotations

import logging
import sys


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("PROXIMUS - AI voice agent for recruiter screening calls")
        print()
        print("Usage: python -m proximus <command> [args]")
        print()
        print("Commands:")
        print("  api              Start the REST API server")
        print("  agent [dev]      Start the voice agent (pass 'dev' for dev mode)")
        print("  sip <subcommand> SIP/Telnyx configuration commands")
        print()
        print("Examples:")
        print("  python -m proximus api")
        print("  python -m proximus agent dev")
        print("  python -m proximus sip setup")
        print("  python -m proximus sip config")
        sys.exit(1)

    command = sys.argv[1]

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if command == "api":
        from proximus.api.main import run_api

        run_api()
    elif command == "agent":
        # LiveKit CLI takes over sys.argv, pass remaining args
        sys.argv = ["proximus-agent"] + sys.argv[2:]
        from proximus.agent.voice import run_agent

        run_agent()
    elif command == "sip":
        sys.argv = ["proximus-sip"] + sys.argv[2:]
        from proximus.cli import run_cli

        sys.exit(run_cli())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
