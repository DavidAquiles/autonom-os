"""The two provider interfaces (KD-7).

No module outside `providers/` may reference Ollama, whisper.cpp, a model name
or a provider-specific field. Callers see only what is declared here.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, Protocol, Sequence


class ProviderUnavailable(Exception):
    """The runtime could not be reached or refused the request."""


class ProviderTimeout(Exception):
    """The runtime did not answer inside the caller's budget."""


class ProviderCancelled(Exception):
    """The caller's cancel token fired (arbiter preemption or a client abort)."""


@dataclass(frozen=True)
class Message:
    role: str  # "system" | "user"
    content: str


@dataclass(frozen=True)
class Transcript:
    text: str
    duration_ms: int
    no_speech: bool


TokenCallback = Callable[[str], None]


class LLMProvider(Protocol):
    async def health(self) -> bool: ...

    async def generate(
        self,
        messages: Sequence[Message],
        *,
        max_tokens: int,
        temperature: float = 0.2,
        timeout_s: float,
        on_token: TokenCallback | None = None,
        cancel: asyncio.Event | None = None,
    ) -> str: ...


class TranscriptionProvider(Protocol):
    async def health(self) -> bool: ...

    async def transcribe(
        self,
        wav_bytes: bytes,
        *,
        language: str,
        timeout_s: float,
        cancel: asyncio.Event | None = None,
    ) -> Transcript: ...


async def race_cancel(coro: Awaitable[object], cancel: asyncio.Event | None):
    """Run `coro`, aborting it as soon as `cancel` is set."""
    task = asyncio.ensure_future(coro)
    if cancel is None:
        return await task
    waiter = asyncio.ensure_future(cancel.wait())
    done, _pending = await asyncio.wait({task, waiter}, return_when=asyncio.FIRST_COMPLETED)
    if task in done:
        waiter.cancel()
        return task.result()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    raise ProviderCancelled()
