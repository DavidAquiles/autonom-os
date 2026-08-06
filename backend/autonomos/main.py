"""Application entry point: one FastAPI app, one worker, one arbiter.

Uvicorn runs with **exactly one worker** (KD-3): the scheduler and the
InferenceArbiter are in-process, and two arbiters is the same as none.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import __version__
from .api import api_router
from .config import get_settings
from .db import init_db
from .errors import ApiError, api_error_handler, unhandled_error_handler
from .scheduler import get_scheduler

log = logging.getLogger("autonomos")

_REASON_BY_PYDANTIC_TYPE = {
    "missing": "required",
    "int_parsing": "not_an_integer",
    "int_type": "not_an_integer",
    "int_from_float": "not_an_integer",
    "float_parsing": "not_an_integer",
    "string_too_long": "too_long",
    "string_type": "required",
    "greater_than": "must_be_positive",
    "greater_than_equal": "must_be_positive",
}


def configure_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    init_db()
    scheduler = get_scheduler()
    if settings.scheduler_enabled:
        await scheduler.start()
    log.info(
        "autonomos-api ready: db=%s tz=%s llm=%s stt=%s",
        settings.db_path,
        settings.app_tz,
        settings.llm_base_url,
        settings.stt_base_url,
    )
    try:
        yield
    finally:
        await scheduler.stop()


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Map FastAPI's own body validation onto the contract's error envelope.

    KD-17: the frontend maps `code` and `fields[].reason`; it never sees a
    framework error shape.
    """
    fields = []
    for error in exc.errors():
        location = [part for part in error.get("loc", []) if part not in ("body", "query")]
        field = str(location[-1]) if location else "body"
        fields.append(
            {"field": field, "reason": _REASON_BY_PYDANTIC_TYPE.get(error.get("type", ""), "required")}
        )
    err = ApiError(400, "validation", "request body failed validation", fields=fields)
    return JSONResponse(status_code=400, content=err.envelope())


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = "not_found" if exc.status_code == 404 else "internal"
    if exc.status_code == 405:
        code = "not_found"
    err = ApiError(exc.status_code, code, str(exc.detail))
    _ = request
    return JSONResponse(status_code=exc.status_code, content=err.envelope())


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Autonom-OS",
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(api_router)
    _mount_spa(app, settings.frontend_dist)
    return app


def _mount_spa(app: FastAPI, dist: Path) -> None:
    """Serve the built SPA from the same origin — no CORS anywhere (KD-2/KD-13).

    The directory belongs to the frontend lane and may not exist yet; the API
    must run either way.
    """
    index = dist / "index.html"
    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404, detail="unknown endpoint")
        candidate = (dist / full_path).resolve() if full_path else index
        try:
            candidate.relative_to(dist.resolve())
        except (ValueError, FileNotFoundError):
            candidate = index
        if candidate.is_file():
            return FileResponse(candidate)
        if index.is_file():
            return FileResponse(index)  # client-side routing owns the path
        raise StarletteHTTPException(
            status_code=404, detail="frontend build not present (FRONTEND_DIST)"
        )


app = create_app()
