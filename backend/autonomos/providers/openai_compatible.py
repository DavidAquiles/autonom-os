"""LLM adapter speaking the OpenAI chat-completions wire format (KD-7).

Today it points at Ollama on 127.0.0.1:11434/v1. llama.cpp `llama-server`,
LM Studio and vLLM are reachable by changing `LLM_BASE_URL`/`LLM_MODEL` only.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Sequence

import httpx

from .base import (
    LLMProvider,
    Message,
    ProviderCancelled,
    ProviderTimeout,
    ProviderUnavailable,
    TokenCallback,
)

log = logging.getLogger("autonomos.providers.llm")


async def _cancellable_lines(response, cancel, loop, deadline):
    """Yield SSE lines, aborting the moment `cancel` fires or the budget ends."""
    iterator = response.aiter_lines().__aiter__()
    while True:
        if cancel is not None and cancel.is_set():
            raise ProviderCancelled()
        remaining = deadline - loop.time()
        if remaining <= 0:
            raise ProviderTimeout("generation exceeded its budget")
        next_line = asyncio.ensure_future(iterator.__anext__())
        waiters = {next_line}
        cancel_wait = None
        if cancel is not None:
            cancel_wait = asyncio.ensure_future(cancel.wait())
            waiters.add(cancel_wait)
        done, _pending = await asyncio.wait(
            waiters, timeout=remaining, return_when=asyncio.FIRST_COMPLETED
        )
        if cancel_wait is not None and cancel_wait in done:
            next_line.cancel()
            raise ProviderCancelled()
        if cancel_wait is not None:
            cancel_wait.cancel()
        if next_line not in done:
            next_line.cancel()
            raise ProviderTimeout("generation exceeded its budget")
        try:
            yield next_line.result()
        except StopAsyncIteration:
            return


class OpenAICompatibleLLM(LLMProvider):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self._base_url}/models")
                return response.status_code < 500
        except Exception:  # any transport failure is "unavailable"
            return False

    async def generate(
        self,
        messages: Sequence[Message],
        *,
        max_tokens: int,
        temperature: float = 0.2,
        timeout_s: float,
        on_token: TokenCallback | None = None,
        cancel: asyncio.Event | None = None,
    ) -> str:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        collected: list[str] = []
        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(timeout_s, 0.1)
        try:
            timeout = httpx.Timeout(connect=5.0, read=timeout_s, write=10.0, pool=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST", f"{self._base_url}/chat/completions", json=payload
                ) as response:
                    if response.status_code >= 400:
                        await response.aread()
                        raise ProviderUnavailable(
                            f"llm http {response.status_code}: {response.text[:200]}"
                        )
                    # Each line is awaited *against* the cancel event rather
                    # than checked between lines. Prompt evaluation emits no
                    # tokens for tens of seconds on this host, so a between-lines
                    # check would leave a preempting transcription waiting for
                    # the next token — measured at ~2 s on 2026-08-05, which is
                    # well past the ~1 s residual R4 budgets for. This keeps
                    # cancellation sub-100 ms whatever phase generation is in.
                    async for line in _cancellable_lines(response, cancel, loop, deadline):
                        if not line or not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        choices = chunk.get("choices") or []
                        if not choices:
                            continue
                        piece = (choices[0].get("delta") or {}).get("content") or ""
                        if piece:
                            collected.append(piece)
                            if on_token is not None:
                                on_token(piece)
        except (ProviderCancelled, ProviderTimeout, ProviderUnavailable):
            raise
        except httpx.TimeoutException as exc:
            raise ProviderTimeout(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(str(exc)) from exc
        return "".join(collected).strip()
