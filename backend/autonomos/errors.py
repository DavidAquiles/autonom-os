"""The error envelope and the closed error-code set (Interface Contract, KD-17).

`message` is a developer string and is never meant to be displayed; the frontend
maps `code` (and `fields[].reason`) to Spanish copy. Machine values a message
needs go in `details`, never inside `reason`.
"""

from __future__ import annotations

from typing import Any, Iterable

from fastapi import Request
from fastapi.responses import JSONResponse

# Closed error-code set — Interface Contract.
ERROR_CODES = frozenset(
    {
        "validation",
        "not_found",
        "conflict",
        "in_use",
        "audio_invalid",
        "audio_too_long",
        "transcription_failed",
        "transcription_timeout",
        "llm_unavailable",
        "llm_timeout",
        "insufficient_data",
        "unverifiable_figures",
        "period_unrecognised",
        "preempted",
        "busy",
        "internal",
    }
)

# Closed `reason` vocabulary for `validation`.
VALIDATION_REASONS = frozenset(
    {
        "required",
        "must_be_positive",
        "not_an_integer",
        "too_long",
        "future_date",
        "blank",
        "unknown_id",
        "duplicate_name",
    }
)


class ApiError(Exception):
    """An error that becomes the contract's error envelope."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str = "",
        *,
        fields: Iterable[dict[str, str]] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        assert code in ERROR_CODES, f"error code outside the closed set: {code}"
        super().__init__(message or code)
        self.status_code = status_code
        self.code = code
        self.message = message or code
        self.fields = list(fields) if fields is not None else None
        self.details = details

    def envelope(self) -> dict[str, Any]:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.code == "validation":
            error["fields"] = self.fields or []
        elif self.fields:
            error["fields"] = self.fields
        error["details"] = self.details if self.details is not None else {}
        return {"error": error}


class ValidationError(ApiError):
    def __init__(self, fields: Iterable[dict[str, str]], message: str = "validation failed"):
        collected = list(fields)
        for f in collected:
            assert f["reason"] in VALIDATION_REASONS, f"unknown reason: {f['reason']}"
        super().__init__(400, "validation", message, fields=collected)


def field_error(field: str, reason: str) -> dict[str, str]:
    return {"field": field, "reason": reason}


class NotFound(ApiError):
    def __init__(self, what: str = "resource"):
        super().__init__(404, "not_found", f"{what} not found")


class Conflict(ApiError):
    def __init__(self, message: str = "conflict"):
        super().__init__(409, "conflict", message)


class InUse(ApiError):
    def __init__(self, affected_expenses: int):
        super().__init__(
            409,
            "in_use",
            "in use by existing expenses; pass confirm=true to archive",
            details={"affected_expenses": affected_expenses},
        )


async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.envelope())


async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    err = ApiError(500, "internal", f"{type(exc).__name__}: {exc}")
    return JSONResponse(status_code=500, content=err.envelope())
