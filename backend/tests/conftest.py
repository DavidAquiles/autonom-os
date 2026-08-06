"""Shared fixtures: an isolated database per test and fake sidecars.

The fakes implement the two provider interfaces of KD-7 and nothing else, which
is what makes the arbiter and the job runner testable without Ollama or whisper
running.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autonomos import arbiter as arbiter_module  # noqa: E402
from autonomos import config, providers  # noqa: E402
from autonomos.db import connection as db_connection  # noqa: E402
from autonomos.providers.base import (  # noqa: E402
    Message,
    ProviderCancelled,
    ProviderUnavailable,
    Transcript,
)


class FakeLLM:
    def __init__(self) -> None:
        self.response = "Gastaste 14.000 pesos en total."
        self.healthy = True
        self.delay_s = 0.0
        self.raise_error: Exception | None = None
        self.calls: list[list[Message]] = []

    async def health(self) -> bool:
        return self.healthy

    async def generate(
        self,
        messages,
        *,
        max_tokens: int,
        temperature: float = 0.2,
        timeout_s: float,
        on_token=None,
        cancel=None,
    ) -> str:
        self.calls.append(list(messages))
        if self.raise_error is not None:
            raise self.raise_error
        elapsed = 0.0
        step = 0.02
        while elapsed < self.delay_s:
            if cancel is not None and cancel.is_set():
                raise ProviderCancelled()
            await asyncio.sleep(step)
            elapsed += step
        if cancel is not None and cancel.is_set():
            raise ProviderCancelled()
        text = self.response if isinstance(self.response, str) else self.response()
        if on_token is not None:
            on_token(text)
        return text


class FakeSTT:
    def __init__(self) -> None:
        self.transcript = "gasté catorce mil pesos en uber con la tarjeta de crédito"
        self.healthy = True
        self.delay_s = 0.0
        self.raise_error: Exception | None = None

    async def health(self) -> bool:
        return self.healthy

    async def transcribe(self, wav_bytes, *, language, timeout_s, cancel=None):
        if self.raise_error is not None:
            raise self.raise_error
        if self.delay_s:
            elapsed = 0.0
            while elapsed < self.delay_s:
                if cancel is not None and cancel.is_set():
                    raise ProviderCancelled()
                await asyncio.sleep(0.02)
                elapsed += 0.02
        return Transcript(text=self.transcript, duration_ms=1000, no_speech=not self.transcript)


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path / "snapshots"))
    monkeypatch.setenv("FRONTEND_DIST", str(tmp_path / "dist"))
    monkeypatch.setenv("SCHEDULER_ENABLED", "0")
    monkeypatch.setenv("APP_TZ", "America/Bogota")
    config.reset_settings()
    db_connection.reset_for_tests()
    arbiter_module.reset_arbiter()
    providers.set_providers(None, None)
    yield
    db_connection.reset_for_tests()
    providers.set_providers(None, None)
    arbiter_module.reset_arbiter()
    config.reset_settings()


@pytest.fixture
def fake_llm():
    llm = FakeLLM()
    providers.set_providers(llm=llm, stt=providers._stt)
    return llm


@pytest.fixture
def fake_stt():
    stt = FakeSTT()
    providers.set_providers(llm=providers._llm, stt=stt)
    return stt


@pytest.fixture
def sidecars(fake_llm, fake_stt):
    providers.set_providers(llm=fake_llm, stt=fake_stt)
    return fake_llm, fake_stt


@pytest.fixture
def db():
    from autonomos.db import get_db

    return get_db()


@pytest.fixture
def client(sidecars):
    from fastapi.testclient import TestClient

    from autonomos.api import health as health_api
    from autonomos.main import create_app

    health_api.invalidate_status_cache()
    with TestClient(create_app()) as test_client:
        yield test_client
    health_api.invalidate_status_cache()


def wav_bytes(seconds: float = 1.0, sample_rate: int = 16000, channels: int = 1,
              bits: int = 16, amplitude: int = 1000) -> bytes:
    """A valid canonical WAV, as the browser produces it (KD-15)."""
    import math
    import struct

    frames = int(seconds * sample_rate)
    body = b"".join(
        struct.pack("<h", int(amplitude * math.sin(i / 20.0))) for i in range(frames)
    )
    block_align = channels * bits // 8
    header = (
        b"RIFF"
        + struct.pack("<I", 36 + len(body))
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, channels, sample_rate,
                      sample_rate * block_align, block_align, bits)
        + b"data"
        + struct.pack("<I", len(body))
    )
    return header + body


__all__ = ["FakeLLM", "FakeSTT", "ProviderUnavailable", "wav_bytes"]
