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
    twilio_phone_number: str = ""   # E.164 format
    twilio_sip_domain: str = ""     # e.g. proximus.pstn.twilio.com
    twilio_termination_uri: str = ""  # SIP termination URI for outbound trunk


    # SIP/Agent Configuration
    agent_name: str = "proximus-agent"
    room_prefix: str = "proximus-call-"
    outbound_trunk_id: str = ""  # LiveKit SIP outbound trunk ID

    # AI Providers
    anthropic_api_key: SecretStr = SecretStr("")
    openai_api_key: SecretStr = SecretStr("")
    ai_provider: Literal["anthropic", "openai"] = "anthropic"

    # Speech Services
    deepgram_api_key: SecretStr = SecretStr("")
    cartesia_api_key: SecretStr = SecretStr("")

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
