"""Anthropic (Claude) AI provider implementation."""

from __future__ import annotations

from collections.abc import AsyncIterator

import anthropic

from proximus.ai.base import AIProvider, Message, Role


class AnthropicProvider(AIProvider):
    """Claude AI provider using the Anthropic API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key.
            model: Model identifier to use.
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, str]]:
        """Convert messages to Anthropic format."""
        return [
            {"role": "user" if msg.role == Role.USER else "assistant", "content": msg.content}
            for msg in messages
            if msg.role != Role.SYSTEM
        ]

    async def generate(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Generate a response using Claude."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=self._convert_messages(messages),
        )
        return response.content[0].text

    async def generate_stream(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream a response using Claude."""
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=self._convert_messages(messages),
        ) as stream:
            async for text in stream.text_stream:
                yield text
