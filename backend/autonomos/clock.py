"""Local-day and local-month arithmetic in APP_TZ.

Design: `clock/` is the **only** place calendar boundaries are computed (4.8).
The server is authoritative for "today" and "this month"; nothing derives a
boundary from a device clock.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .config import get_settings

_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

MONTH_NAMES_ES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def tz() -> ZoneInfo:
    return ZoneInfo(get_settings().app_tz)


def now() -> datetime:
    """Timezone-aware 'now' in APP_TZ."""
    return datetime.now(tz())


def now_iso() -> str:
    """ISO-8601 with offset — the wire format for every timestamp.

    Millisecond precision, not seconds: `GET /api/journal`'s cursor is a
    `written_at` value, so two entries written in the same second must still
    order and paginate distinctly.
    """
    return now().isoformat(timespec="milliseconds")


def today() -> date:
    return now().date()


def today_str() -> str:
    return today().isoformat()


def current_month() -> str:
    return today().strftime("%Y-%m")


def parse_date(value: str) -> date | None:
    if not _DATE_RE.match(value or ""):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def is_valid_month(value: str) -> bool:
    return bool(_MONTH_RE.match(value or ""))


def month_bounds(month_key: str) -> tuple[str, str]:
    """First and last local day of `YYYY-MM`, inclusive, as YYYY-MM-DD."""
    if not is_valid_month(month_key):
        raise ValueError(f"bad month key: {month_key}")
    year, mon = (int(p) for p in month_key.split("-"))
    start = date(year, mon, 1)
    end = date(year + (mon == 12), 1 if mon == 12 else mon + 1, 1) - timedelta(days=1)
    return start.isoformat(), end.isoformat()


def month_key_of(d: date) -> str:
    return d.strftime("%Y-%m")


def previous_month(month_key: str) -> str:
    year, mon = (int(p) for p in month_key.split("-"))
    return f"{year - 1}-12" if mon == 1 else f"{year}-{mon - 1:02d}"


def next_month(month_key: str) -> str:
    year, mon = (int(p) for p in month_key.split("-"))
    return f"{year + 1}-01" if mon == 12 else f"{year}-{mon + 1:02d}"


def month_label_es(month_key: str) -> str:
    """`2025-07` -> `julio de 2025`. Used for facts.period_label."""
    year, mon = (int(p) for p in month_key.split("-"))
    return f"{MONTH_NAMES_ES[mon - 1]} de {year}"


def months_between(first: str, last: str) -> list[str]:
    """Inclusive list of month keys from `first` to `last` (empty if reversed)."""
    out: list[str] = []
    cur = first
    while cur <= last:
        out.append(cur)
        cur = next_month(cur)
    return out


def completed_months_until_now() -> str:
    """The last *completed* calendar month (i.e. the month before the current one)."""
    return previous_month(current_month())


def week_bounds(d: date) -> tuple[str, str]:
    """Monday..Sunday containing `d`."""
    start = d - timedelta(days=d.weekday())
    return start.isoformat(), (start + timedelta(days=6)).isoformat()
