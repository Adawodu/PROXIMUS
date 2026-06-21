"""OpenAI AI provider implementation."""

from __future__ import annotations

from collections.abc import AsyncIterator

import openai

from proximus.ai.base import AIProvider, Message


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key.
            model: Model identifier to use.
        """
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    def _convert_messages(
        self, messages: list[Message], system_prompt: str | None = None
    ) -> list[dict[str, str]]:
        """Convert messages to OpenAI format."""
        result: list[dict[str, str]] = []

        if system_prompt:
            result.append({"role": "system", "content": system_prompt})

        for msg in messages:
            role = msg.role.value
            result.append({"role": role, "content": msg.content})

        return result

    async def generate(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Generate a response using GPT."""
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=self._convert_messages(messages, system_prompt),
        )
        return response.choices[0].message.content or ""

    async def generate_stream(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream a response using GPT."""
        stream = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=self._convert_messages(messages, system_prompt),
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
