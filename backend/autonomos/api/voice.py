"""`POST /api/voice/transcribe` (Requirements 8, 9, 10).

**This endpoint writes nothing to the database.** There is no endpoint that
turns audio into a saved record: it returns a transcript and, for the expense
context, a rules-derived draft. Creation always goes through `POST /api/expenses`
or `POST /api/journal` exactly as the manual path does (8.3, 8.6, 9.5, 10.4).

For `journal` and `question` the transcript is returned verbatim — the LLM is
not consulted, not for cleanup, not for punctuation (KD-9 enforces 10.2 by the
absence of a code path).
"""

from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter, File, Form, UploadFile

from ..arbiter import ArbiterTimeout, JobKind, get_arbiter
from ..audio import looks_hallucinated, validate_audio
from ..config import get_settings
from ..db import get_db
from ..errors import ApiError, ValidationError, field_error
from ..parsing.extractor import parse_expense_text
from ..providers import ProviderCancelled, ProviderTimeout, ProviderUnavailable, get_stt
from .expenses import draft_to_wire
from .models import TranscribeResponse

log = logging.getLogger("autonomos.api.voice")

router = APIRouter()

VALID_CONTEXTS = ("expense", "journal", "question")


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(...),
    context: str = Form(...),
) -> dict:
    settings = get_settings()
    started = time.monotonic()
    if context not in VALID_CONTEXTS:
        raise ValidationError([field_error("context", "required")])

    data = await audio.read()
    info = validate_audio(
        data,
        max_audio_s=settings.max_audio_s,
        max_bytes=settings.max_audio_bytes,
        min_audio_s=settings.min_audio_s,
    )

    cancel = asyncio.Event()
    arbiter = get_arbiter()
    try:
        # Transcription never waits behind background work and preempts a
        # running question (KD-12). The only wait it can meet is the sidecar's.
        lease = await arbiter.acquire(
            JobKind.TRANSCRIPTION, cancel, wait_timeout_s=settings.stt_timeout_s
        )
    except ArbiterTimeout:
        raise ApiError(504, "transcription_timeout", "arbiter slot never freed")

    try:
        result = await get_stt().transcribe(
            data,
            language=settings.stt_language,
            timeout_s=settings.stt_timeout_s,
            cancel=cancel,
        )
    except ProviderTimeout:
        raise ApiError(504, "transcription_timeout", "sidecar exceeded STT_TIMEOUT_S")
    except ProviderCancelled:
        # The client aborted (8.9): nothing was written, nothing is returned.
        raise ApiError(422, "transcription_failed", "cancelled by the client")
    except ProviderUnavailable as exc:
        raise ApiError(422, "transcription_failed", str(exc))
    except asyncio.CancelledError:
        cancel.set()
        raise
    finally:
        arbiter.release(lease)

    transcript = (result.text or "").strip()
    if result.no_speech or looks_hallucinated(transcript):
        raise ApiError(422, "transcription_failed", "no usable speech in the audio")

    elapsed_ms = int((time.monotonic() - started) * 1000)
    # R9 asks for elapsed_ms logged from day one: the measured figures are
    # single-run benchmarks, not a p95 under contention.
    log.info(
        "transcribe context=%s audio_ms=%d elapsed_ms=%d chars=%d",
        context,
        info.duration_ms,
        elapsed_ms,
        len(transcript),
    )

    draft = None
    if context == "expense":
        draft = draft_to_wire(parse_expense_text(get_db(), transcript))

    return {
        "transcript": transcript,
        "audio_ms": info.duration_ms,
        "elapsed_ms": elapsed_ms,
        "draft": draft,
    }
