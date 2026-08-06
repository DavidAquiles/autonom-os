"""The catch-up scan, summary generation and the nightly snapshot (KD-12, KD-4)."""

from __future__ import annotations

import asyncio
import json

import pytest

from autonomos import scheduler as scheduler_module
from autonomos.arbiter import JobKind, get_arbiter
from autonomos.clock import now_iso
from autonomos.config import get_settings
from autonomos.db import get_db
from autonomos.insights.runner import run_summary, sweep_on_startup
from autonomos.repo import summaries as summaries_repo


def add_expense(conn, spent_on: str, amount: int = 10000, category_id: int = 1) -> None:
    ts = now_iso()
    conn.execute(
        "INSERT INTO expenses(amount_cop, category_id, payment_method_id, spent_on, "
        "description, source, created_at, updated_at) VALUES(?,?,?,?,?,'manual',?,?)",
        (amount, category_id, 1, spent_on, "prueba", ts, ts),
    )


def add_entry(conn, written_at: str, text: str = "Hoy escribí algo.") -> None:
    conn.execute(
        "INSERT INTO journal_entries(text, written_at, source, created_at, updated_at) "
        "VALUES(?,?,'manual',?,?)",
        (text, written_at, written_at, written_at),
    )


def test_scan_finds_every_completed_month_with_no_row(db):
    add_expense(db, "2026-05-10")
    add_expense(db, "2026-06-11")
    months = scheduler_module.pending_summary_months()
    assert "2026-05" in months and "2026-06" in months
    assert "2026-08" not in months  # the current month is not complete


def test_scan_skips_a_month_that_already_has_a_finished_summary(db):
    add_expense(db, "2026-05-10")
    summaries_repo.start(db, "2026-05")
    summaries_repo.finish_ready(db, "2026-05", "listo", {}, "modelo")
    assert "2026-05" not in scheduler_module.pending_summary_months()


def test_a_failed_month_is_retried_up_to_three_times(db):
    add_expense(db, "2026-05-10")
    for attempt in range(1, 4):
        summaries_repo.start(db, "2026-05")
        summaries_repo.finish_failed(db, "2026-05", "llm_timeout")
        pending = scheduler_module.pending_summary_months()
        if attempt < 3:
            assert "2026-05" in pending, f"attempt {attempt} should be retried"
        else:
            assert "2026-05" not in pending  # nothing loops after the third


def test_startup_deletes_orphaned_generating_rows(db):
    summaries_repo.start(db, "2026-05")
    assert summaries_repo.get(db, "2026-05")["status"] == "generating"
    sweep_on_startup()
    assert summaries_repo.get(db, "2026-05") is None


def test_startup_sweep_fails_jobs_left_running(db):
    from autonomos.repo import jobs as jobs_repo

    row = jobs_repo.create(db, "¿cuánto gasté?", "text")
    jobs_repo.mark_running(db, row["id"], None)
    sweep_on_startup()
    assert jobs_repo.get(db, row["id"])["status"] == "failed"


async def test_11_14_a_summary_covers_spending_and_journal(db, fake_llm):
    add_expense(db, "2026-05-10", amount=25000)
    add_entry(db, "2026-05-10T21:00:00.000-05:00", "Estuve pensando en el trabajo.")
    fake_llm.response = "En mayo gastaste 25.000 pesos y escribiste sobre el trabajo."

    assert await run_summary("2026-05") == "ready"
    row = summaries_repo.get(db, "2026-05")
    assert row["status"] == "ready"
    assert row["text"] == fake_llm.response
    facts = json.loads(row["facts_json"])
    assert facts["domain"] == "both"
    assert facts["total_cop"] == 25000
    assert facts["journal_entries_used"] == 1


async def test_a_month_with_no_data_is_stored_as_empty(db, fake_llm):
    add_expense(db, "2026-06-10")
    assert await run_summary("2026-05") == "empty"
    assert summaries_repo.get(db, "2026-05")["status"] == "empty"
    assert fake_llm.calls == []


async def test_a_cancelled_summary_deletes_its_row_and_burns_no_attempt(db, fake_llm):
    add_expense(db, "2026-05-10")
    fake_llm.delay_s = 5.0
    task = asyncio.ensure_future(run_summary("2026-05"))
    await asyncio.sleep(0.15)

    # An interactive arrival cancels the in-flight summary immediately.
    arbiter = get_arbiter()
    lease = await arbiter.acquire(JobKind.TRANSCRIPTION, asyncio.Event())
    assert await asyncio.wait_for(task, 3.0) == "cancelled"
    arbiter.release(lease)

    assert summaries_repo.get(db, "2026-05") is None
    assert "2026-05" in scheduler_module.pending_summary_months()


async def test_a_summary_with_an_unverifiable_figure_fails_explicitly(db, fake_llm):
    add_expense(db, "2026-05-10", amount=25000)
    fake_llm.response = "En mayo gastaste 88.888 pesos."
    assert await run_summary("2026-05") == "failed"
    row = summaries_repo.get(db, "2026-05")
    assert row["error_code"] == "unverifiable_figures"
    assert len(fake_llm.calls) == 2


def test_nightly_snapshot_writes_a_file_and_prunes(db, monkeypatch):
    settings = get_settings()
    add_expense(db, "2026-05-10")
    path = scheduler_module.take_snapshot()
    assert path is not None and path.exists()

    for day in range(1, 12):
        (settings.snapshot_dir / f"2026-01-{day:02d}.sqlite").write_bytes(b"x")
    scheduler_module.prune_snapshots()
    remaining = list(settings.snapshot_dir.glob("*.sqlite"))
    assert len(remaining) == settings.snapshot_keep_days


def test_snapshot_contains_the_data(db):
    import sqlite3

    add_expense(db, "2026-05-10", amount=31337)
    path = scheduler_module.take_snapshot()
    copy = sqlite3.connect(path)
    try:
        total = copy.execute("SELECT SUM(amount_cop) FROM expenses").fetchone()[0]
    finally:
        copy.close()
    assert total == 31337


@pytest.mark.parametrize("hour,expected", [(2, False), (3, True)])
def test_snapshot_is_due_after_the_nightly_hour(monkeypatch, hour, expected):
    from datetime import datetime

    from autonomos import clock

    fixed = datetime(2026, 8, 5, hour, 30, tzinfo=clock.tz())
    monkeypatch.setattr(scheduler_module, "now", lambda: fixed)
    assert scheduler_module.snapshot_due() is expected


async def test_the_tick_starts_generation_for_a_pending_month(db, fake_llm):
    add_expense(db, "2026-05-10")
    fake_llm.response = "En mayo gastaste 10.000 pesos."
    scheduler = scheduler_module.Scheduler()
    await scheduler.tick()
    assert scheduler._worker is not None
    await asyncio.wait_for(scheduler._worker, 5.0)
    assert summaries_repo.get(db, "2026-05")["status"] == "ready"
