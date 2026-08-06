"""`/api/summary/day` and `/api/summary/month` (Requirement 4).

Both boundaries come from `clock`, which is the only place a calendar day or
month is computed (4.8) — the phone never derives one from the device clock.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from ..clock import current_month, is_valid_month, parse_date, today_str
from ..db import get_db
from ..errors import ValidationError, field_error
from ..repo import expenses as repo
from .models import DaySummary, MonthSummary

router = APIRouter()


@router.get("/day", response_model=DaySummary)
def day_summary(date: str | None = Query(None)) -> dict:
    day = date or today_str()
    if parse_date(day) is None:
        raise ValidationError([field_error("date", "required")])
    return repo.day_summary(get_db(), day)


@router.get("/month", response_model=MonthSummary)
def month_summary(month: str | None = Query(None)) -> dict:
    key = month or current_month()
    if not is_valid_month(key):
        raise ValidationError([field_error("month", "required")])
    return repo.month_summary(get_db(), key)
