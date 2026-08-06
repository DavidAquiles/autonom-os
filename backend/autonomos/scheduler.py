"""In-process scheduler (KD-12): boot catch-up, 15-minute tick, nightly snapshot.

Not cron, not a systemd timer, not APScheduler: a separate entry point would
have its own DB connection and could not see the InferenceArbiter, and two
generations at once on 8 cores is the failure A22 exists to prevent.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from .clock import (
    completed_months_until_now,
    month_key_of,
    months_between,
    now,
    today_str,
)
from .config import get_settings
from .db import connect, get_db
from .db.connection import close_thread_db
from .insights.runner import run_summary, sweep_on_startup
from .repo import expenses as expenses_repo
from .repo import journal as journal_repo
from .repo import summaries as summaries_repo

log = logging.getLogger("autonomos.scheduler")

SNAPSHOT_HOUR = 3
MAX_CANCEL_RETRIES = 5


def pending_summary_months() -> list[str]:
    """Completed calendar months between the first recorded data and last month
    that lack a *finished* summary — no row, or `failed` with attempts < 3."""
    settings = get_settings()
    conn = get_db()
    first_expense = expenses_repo.first_expense_date(conn)
    first_entry = journal_repo.first_entry_date(conn)
    firsts = [d for d in (first_expense, first_entry) if d]
    if not firsts:
        return []
    first_month = min(firsts)[:7]
    last_month = completed_months_until_now()
    if first_month > last_month:
        return []
    candidates = months_between(first_month, last_month)
    return summaries_repo.months_needing_summary(
        conn, candidates, settings.summary_max_attempts
    )


def snapshot_due() -> bool:
    settings = get_settings()
    target = settings.snapshot_dir / f"{today_str()}.sqlite"
    return now().hour >= SNAPSHOT_HOUR and not target.exists()


def take_snapshot() -> Path | None:
    """Nightly `VACUUM INTO`, keeping the last 7 days (KD-4, approved at the gate)."""
    settings = get_settings()
    settings.snapshot_dir.mkdir(parents=True, exist_ok=True)
    target = settings.snapshot_dir / f"{today_str()}.sqlite"
    if target.exists():
        return target
    conn = connect(settings.db_path)
    try:
        conn.execute("VACUUM INTO ?", (str(target),))
    finally:
        conn.close()
    prune_snapshots()
    log.info("snapshot written: %s", target)
    return target


def prune_snapshots() -> int:
    settings = get_settings()
    files = sorted(settings.snapshot_dir.glob("*.sqlite"))
    excess = files[: max(0, len(files) - settings.snapshot_keep_days)]
    for path in excess:
        path.unlink(missing_ok=True)
    return len(excess)


class Scheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._worker: asyncio.Task | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return  # idempotent: two listeners, one scheduler (KD-3)
        sweep_on_startup()
        self._stop.clear()
        self._task = asyncio.ensure_future(self._loop())

    async def stop(self) -> None:
        self._stop.set()
        for task in (self._task, self._worker):
            if task is not None and not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        self._task = None
        self._worker = None

    async def _loop(self) -> None:
        settings = get_settings()
        while not self._stop.is_set():
            try:
                await self.tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("scheduler tick failed")
            try:
                await asyncio.wait_for(self._stop.wait(), settings.scheduler_tick_s)
            except asyncio.TimeoutError:
                pass

    async def tick(self) -> None:
        if snapshot_due():
            await asyncio.to_thread(_snapshot_in_thread)
        if self._worker is not None and not self._worker.done():
            return
        if pending_summary_months():
            self._worker = asyncio.ensure_future(self._drain_summaries())

    async def _drain_summaries(self) -> None:
        """Generate every pending month, one at a time, newest month first.

        A cancelled month is retried inside this run; the arbiter's 60-second
        quiet period is what stops a run of back-to-back captures livelocking it.
        """
        cancelled_retries = 0
        while not self._stop.is_set():
            months = pending_summary_months()
            if not months:
                return
            month = months[-1]
            outcome = await run_summary(month)
            log.info("summary %s -> %s", month, outcome)
            if outcome == "cancelled":
                cancelled_retries += 1
                if cancelled_retries >= MAX_CANCEL_RETRIES:
                    return
            elif outcome == "not_started":
                return


def _snapshot_in_thread() -> None:
    try:
        take_snapshot()
    finally:
        close_thread_db()


_scheduler: Scheduler | None = None


def get_scheduler() -> Scheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


def month_of_today() -> str:
    return month_key_of(now().date())
