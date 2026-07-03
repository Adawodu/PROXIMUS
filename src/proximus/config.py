"""Configuration management using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LiveKit
    livekit_url: str = "wss://localhost:7880"
    livekit_api_key: str = ""
    livekit_api_secret: SecretStr = SecretStr("")
    livekit_sip_uri: str = ""  # e.g. your-project.sip.livekit.cloud (for setup instructions)

    # SIP Provider: "telnyx" or "twilio"
    sip_provider: Literal["telnyx", "twilio"] = "telnyx"

    # Telnyx
    telnyx_api_key: SecretStr = SecretStr("")
    telnyx_sip_uri: str = ""
    telnyx_sip_username: str = ""
    telnyx_sip_password: SecretStr = SecretStr("")
    telnyx_phone_number: str = ""  # Your Telnyx phone number (E.164 format)
    telnyx_credential_connection_id: str = (
        ""  # Telnyx credential connection ID (for caller ID / ANI override)
    )

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: SecretStr = SecretStr("")
    twilio_phone_number: str = ""  # Your Twilio phone number (E.164 format)
    twilio_termination_uri: str = ""  # SIP termination URI e.g. your-trunk.pstn.twilio.com
    # Twilio Credential List credentials for SIP trunk digest authentication.
    # Create in Twilio Console: Elastic SIP Trunking -> your trunk -> Authentication
    # -> Credential Lists. These are NOT the Account SID / Auth Token.
    twilio_sip_username: str = ""
    twilio_sip_password: SecretStr = SecretStr("")

    # SIP/Agent Configuration
    agent_name: str = "proximus-agent"
    room_prefix: str = "proximus-call-"
    outbound_trunk_id: str = ""  # LiveKit SIP outbound trunk ID

    # AI Providers
    anthropic_api_key: SecretStr = SecretStr("")
    openai_api_key: SecretStr = SecretStr("")
    ai_provider: Literal["anthropic", "openai"] = "anthropic"
    # LLM model per provider. Default to a low-latency model — voice turns are short
    # (2-3 sentences) and every 100ms is audible on a live call.
    anthropic_model: str = "claude-haiku-4-5"
    openai_model: str = "gpt-4o"

    # Speech Services
    deepgram_api_key: SecretStr = SecretStr("")
    cartesia_api_key: SecretStr = SecretStr("")

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    # API authentication. When set, every non-public route requires a matching
    # X-API-Key header. Left empty the API is unauthenticated — fine for local dev,
    # but set this before exposing the server (outbound calls cost real money).
    api_key: SecretStr = SecretStr("")
    # Comma-separated list of allowed CORS origins for the web dashboard.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # Max outbound calls allowed per rolling minute (0 disables the limit).
    outbound_rate_limit_per_min: int = 10

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
