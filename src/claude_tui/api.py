"""AsyncAnthropic wrapper with streaming support."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any, Callable

import anthropic
from anthropic import AsyncAnthropic

from claude_tui.config import config


def get_client() -> AsyncAnthropic:
    """Return a configured AsyncAnthropic client."""
    return AsyncAnthropic(api_key=config.api_key)


async def stream_response(
    messages: list[dict[str, Any]],
    model: str,
    system: str,
    max_tokens: int,
    on_chunk: Callable[[str], None],
) -> tuple[str, int]:
    """
    Stream a response from the Claude API.

    Args:
        messages: Anthropic-format messages array
        model: Model ID string
        system: System prompt
        max_tokens: Max tokens for the response
        on_chunk: Callback called with the *full accumulated text* after each chunk

    Returns:
        Tuple of (full_text, total_input_tokens + output_tokens)
    """
    client = get_client()
    accumulated = ""
    input_tokens = 0
    output_tokens = 0

    async with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    ) as stream:
        async for event in stream:
            match event.type:
                case "message_start":
                    if hasattr(event, "message") and hasattr(event.message, "usage"):
                        input_tokens = event.message.usage.input_tokens
                case "content_block_delta":
                    if hasattr(event, "delta") and hasattr(event.delta, "text"):
                        accumulated += event.delta.text
                        on_chunk(accumulated)
                case "message_delta":
                    if hasattr(event, "usage"):
                        output_tokens = event.usage.output_tokens

    return accumulated, input_tokens + output_tokens


async def simple_response(
    messages: list[dict[str, Any]],
    model: str,
    system: str,
    max_tokens: int,
) -> tuple[str, int]:
    """Non-streaming response (for fallback or short requests)."""
    client = get_client()
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text
    total_tokens = response.usage.input_tokens + response.usage.output_tokens
    return text, total_tokens
