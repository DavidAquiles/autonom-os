"""`GET /api/health` and `GET /api/status` (13.2, 13.3, 11.4, 8.4)."""

from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter

from ..clock import now_iso
from ..config import as_origin, get_settings, lan_origin
from ..providers import get_llm, get_stt
from .models import Health, Status

router = APIRouter()

_status_cache: tuple[float, dict] | None = None
_HEALTH_PROBE_TIMEOUT_S = 2.5


@router.get("/health", response_model=Health)
def health() -> dict:
    """Also advertises both origins, so the client can learn the *other* one
    while the server is still reachable (KD-2 mechanism 1, 13.8).

    Both come from server configuration and **neither is derived from the
    request**: a client that can reach one origin cannot supply the other, and
    a `Host` header would echo back the origin the client is already on — which
    is precisely the one that is of no use during an outage.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "server_time": now_iso(),
        "tz": settings.app_tz,
        "version": settings.version,
        "origins": {
            "primary": as_origin(settings.public_url),
            # null whenever the fallback listener is not actually running:
            # advertising an origin nothing listens on is a lie the client
            # would act on during an outage.
            "lan": lan_origin(settings),
        },
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
