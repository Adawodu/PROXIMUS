"""Provider-agnostic AI layer."""

from __future__ import annotations

from proximus.ai.base import AIProvider, Message, Role
from proximus.config import get_settings


def get_ai_provider() -> AIProvider:
    """Factory function to get the configured AI provider."""
    settings = get_settings()
    provider_name = settings.ai_provider

    if provider_name == "anthropic":
        from proximus.ai.anthropic import AnthropicProvider

        return AnthropicProvider(api_key=settings.anthropic_api_key.get_secret_value())
    elif provider_name == "openai":
        from proximus.ai.openai import OpenAIProvider

        return OpenAIProvider(api_key=settings.openai_api_key.get_secret_value())
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")


__all__ = ["AIProvider", "Message", "Role", "get_ai_provider"]
