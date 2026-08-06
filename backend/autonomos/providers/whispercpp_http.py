"""Transcription adapter for the whisper.cpp `whisper-server` sidecar (KD-5).

The sidecar is started with `-l es` and 6 threads; there is no `--no-translate`
flag in this build, and `-l es` alone is what satisfies 8.7. Audio is forwarded
from memory and never written to disk (15.1).
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from .base import (
    ProviderCancelled,
    ProviderTimeout,
    ProviderUnavailable,
    Transcript,
    TranscriptionProvider,
    race_cancel,
)

log = logging.getLogger("autonomos.providers.stt")


class WhisperCppHttp(TranscriptionProvider):
    def __init__(self, base_url: str, inference_path: str = "/inference") -> None:
        self._base_url = base_url.rstrip("/")
        self._inference_path = inference_path

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # The sidecar serves a small static page at the root; any answer
                # that is not a transport failure means the process is up.
                response = await client.get(f"{self._base_url}/")
                return response.status_code < 500
        except Exception:
            return False

    async def transcribe(
        self,
        wav_bytes: bytes,
        *,
        language: str,
        timeout_s: float,
        cancel: asyncio.Event | None = None,
    ) -> Transcript:
        async def _call() -> Transcript:
            timeout = httpx.Timeout(connect=5.0, read=timeout_s, write=20.0, pool=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self._base_url}{self._inference_path}",
                    files={"file": ("audio.wav", wav_bytes, "audio/wav")},
                    data={
                        "response_format": "json",
                        "language": language,
                        "temperature": "0.0",
                        "no_timestamps": "true",
                    },
                )
                if response.status_code >= 400:
                    raise ProviderUnavailable(
                        f"stt http {response.status_code}: {response.text[:200]}"
                    )
                body = response.json()
            text = (body.get("text") or "").strip()
            return Transcript(text=text, duration_ms=0, no_speech=not text)

        try:
            return await race_cancel(_call(), cancel)
        except (ProviderCancelled, ProviderUnavailable):
            raise
        except httpx.TimeoutException as exc:
            raise ProviderTimeout(str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(str(exc)) from exc
