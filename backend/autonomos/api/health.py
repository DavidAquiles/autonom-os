"""`GET /api/health` and `GET /api/status` (13.2, 13.3, 11.4, 8.4)."""

from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter

from ..clock import now_iso
from ..config import get_settings
from ..providers import get_llm, get_stt
from .models import Health, Status

router = APIRouter()

_status_cache: tuple[float, dict] | None = None
_HEALTH_PROBE_TIMEOUT_S = 2.5


@router.get("/health", response_model=Health)
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "server_time": now_iso(),
        "tz": settings.app_tz,
        "version": settings.version,
    }


async def _probe(coro) -> str:
    try:
        ok = await asyncio.wait_for(coro, _HEALTH_PROBE_TIMEOUT_S)
        return "ok" if ok else "unavailable"
    except Exception:
        return "unavailable"


async def current_status(force: bool = False) -> dict:
    """Cached ~30 s; never blocks a request for longer than a probe timeout."""
    global _status_cache
    settings = get_settings()
    now = time.monotonic()
    if not force and _status_cache and now - _status_cache[0] < settings.status_cache_s:
        return _status_cache[1]
    transcription, llm = await asyncio.gather(
        _probe(get_stt().health()), _probe(get_llm().health())
    )
    payload = {
        "transcription": transcription,
        "llm": llm,
        "checked_at": now_iso(),
    }
    _status_cache = (now, payload)
    return payload


def invalidate_status_cache() -> None:
    global _status_cache
    _status_cache = None


@router.get("/status", response_model=Status)
async def status() -> dict:
    return await current_status()
