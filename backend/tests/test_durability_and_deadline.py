"""Restart durability (14.1) and the answer deadline arithmetic (KD-11)."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta

from autonomos.clock import now
from autonomos.config import get_settings
from autonomos.db import connection as db_connection
from autonomos.db import get_db
from autonomos.insights import runner
from autonomos.repo import jobs as jobs_repo


def test_14_1_records_survive_a_process_restart(client):
    expense = client.post(
        "/api/expenses",
        json={"amount_cop": 14000, "category_id": 1, "payment_method_id": 1},
    ).json()
    entry = client.post("/api/journal", json={"text": "Sigo aquí mañana."}).json()

    # Drop every cached connection, exactly as a restart would.
    db_connection.reset_for_tests()

    assert client.get(f"/api/expenses/{expense['id']}").json()["amount_cop"] == 14000
    assert client.get(f"/api/journal/{entry['id']}").json()["text"] == "Sigo aquí mañana."


def test_wal_and_durability_pragmas_are_on(db):
    assert db.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert int(db.execute("PRAGMA synchronous").fetchone()[0]) == 2  # FULL
    assert int(db.execute("PRAGMA foreign_keys").fetchone()[0]) == 1


def test_14_3_nothing_prunes_expenses_or_entries(db):
    """No expiry, archival or pruning job exists for user records."""
    import inspect

    from autonomos import scheduler

    source = inspect.getsource(scheduler)
    assert "DELETE FROM expenses" not in source
    assert "DELETE FROM journal_entries" not in source


async def test_a_job_that_cannot_finish_in_time_never_starts_generation(db, fake_llm):
    """KD-11: below `LLM_MIN_START_BUDGET_S` the job terminates with
    `llm_timeout` rather than starting a doomed generation."""
    settings = get_settings()
    db.execute(
        "INSERT INTO expenses(amount_cop, category_id, payment_method_id, spent_on, "
        "source, created_at, updated_at) VALUES(10000,1,1,?, 'manual', ?, ?)",
        (now().date().isoformat(), now().isoformat(), now().isoformat()),
    )
    row = jobs_repo.create(db, "¿cuánto gasté hoy?", "text")
    stale = now() - timedelta(seconds=settings.llm_deadline_answer_s - 5)
    db.execute(
        "UPDATE insight_jobs SET created_at = ? WHERE id = ?",
        (stale.isoformat(timespec="milliseconds"), row["id"]),
    )

    await runner._run_question(row["id"], "¿cuánto gasté hoy?", asyncio.Event())

    finished = jobs_repo.get(db, row["id"])
    assert finished["status"] == "failed"
    assert finished["error_code"] == "llm_timeout"
    assert fake_llm.calls == []


async def test_a_job_with_budget_left_does_generate(db, fake_llm):
    db.execute(
        "INSERT INTO expenses(amount_cop, category_id, payment_method_id, spent_on, "
        "source, created_at, updated_at) VALUES(10000,1,1,?, 'manual', ?, ?)",
        (now().date().isoformat(), now().isoformat(), now().isoformat()),
    )
    fake_llm.response = "Hoy gastaste 10.000 pesos."
    row = jobs_repo.create(db, "¿cuánto gasté hoy?", "text")
    await runner._run_question(row["id"], "¿cuánto gasté hoy?", asyncio.Event())
    finished = jobs_repo.get(db, row["id"])
    assert finished["status"] == "done"
    assert finished["answer"] == "Hoy gastaste 10.000 pesos."


def _seed_today(db) -> None:
    db.execute(
        "INSERT INTO expenses(amount_cop, category_id, payment_method_id, spent_on, "
        "source, created_at, updated_at) VALUES(10000,1,1,?, 'manual', ?, ?)",
        (now().date().isoformat(), now().isoformat(), now().isoformat()),
    )


async def test_f1_the_guard_retry_cannot_push_the_job_past_its_deadline(
    db, fake_llm, monkeypatch
):
    """AC 11.12 / KD-11. The strict retry inherits what is left of the deadline,
    not a fresh allowance.

    Against the original defect (`budget_s = budget_s - 1.0`) the retry started
    with ~104 s of nominal budget however long the first attempt ran, and the
    `< llm_min_start_budget_s` check compared that decremented duration rather
    than elapsed time, so it could never fire. Here the first generation eats
    almost the whole deadline and then fails the guard: the retry must not run.
    """
    from autonomos.config import reset_settings

    monkeypatch.setenv("LLM_DEADLINE_ANSWER_S", "3")
    monkeypatch.setenv("LLM_MIN_START_BUDGET_S", "1")
    reset_settings()
    settings = get_settings()
    assert (settings.llm_deadline_answer_s, settings.llm_min_start_budget_s) == (3.0, 1.0)

    _seed_today(db)
    fake_llm.delay_s = 2.4  # leaves ~0.6 s of the 3 s deadline
    fake_llm.response = "Gastaste 987.654 pesos hoy."  # never in the fact set

    row = jobs_repo.create(db, "¿cuánto gasté hoy?", "text")
    created_at = datetime.fromisoformat(row["created_at"]).timestamp()
    await runner._run_question(row["id"], "¿cuánto gasté hoy?", asyncio.Event())
    finished_at = time.time()

    assert len(fake_llm.calls) == 1, "the retry ran with no deadline left for it"
    elapsed = finished_at - created_at
    assert elapsed <= settings.llm_deadline_answer_s + 0.75, (
        f"job ran {elapsed:.1f}s against a {settings.llm_deadline_answer_s}s deadline"
    )
    assert jobs_repo.get(db, row["id"])["status"] == "failed"
    assert jobs_repo.get(db, row["id"])["error_code"] == "llm_timeout"


async def test_f1_a_retry_that_does_fit_still_runs_and_gets_only_what_is_left(
    db, fake_llm, monkeypatch
):
    """The fix must not disable the retry — only bound it. With the whole
    deadline available, the strict second attempt runs, and its timeout is
    strictly smaller than the first's because time has passed."""
    from autonomos.config import reset_settings

    monkeypatch.setenv("LLM_DEADLINE_ANSWER_S", "30")
    monkeypatch.setenv("LLM_MIN_START_BUDGET_S", "1")
    reset_settings()

    _seed_today(db)
    fake_llm.delay_s = 0.3
    fake_llm.response = "Gastaste 987.654 pesos hoy."

    row = jobs_repo.create(db, "¿cuánto gasté hoy?", "text")
    await runner._run_question(row["id"], "¿cuánto gasté hoy?", asyncio.Event())

    assert len(fake_llm.calls) == 2  # one retry, with the stricter prompt
    assert fake_llm.timeouts[1] < fake_llm.timeouts[0]
    assert jobs_repo.get(db, row["id"])["error_code"] == "unverifiable_figures"


async def test_the_provider_is_never_handed_a_timestamp_as_a_timeout(db, fake_llm):
    """A budget that is secretly an absolute epoch time still "works": the call
    succeeds and every status assertion passes, while generation is bounded at
    ~56 years instead of 110 seconds. Nothing else in this suite can see that,
    so this asserts the quantity itself."""
    settings = get_settings()
    _seed_today(db)
    fake_llm.response = "Hoy gastaste 10.000 pesos."

    row = jobs_repo.create(db, "¿cuánto gasté hoy?", "text")
    await runner._run_question(row["id"], "¿cuánto gasté hoy?", asyncio.Event())

    assert fake_llm.timeouts, "the provider was never called"
    for timeout in fake_llm.timeouts:
        assert 0 < timeout <= settings.llm_deadline_answer_s, (
            f"timeout_s={timeout} is not a duration inside the "
            f"{settings.llm_deadline_answer_s}s answer window"
        )


async def test_summary_generation_is_also_handed_a_duration_not_a_timestamp(
    db, fake_llm
):
    from autonomos.insights.runner import run_summary

    settings = get_settings()
    db.execute(
        "INSERT INTO expenses(amount_cop, category_id, payment_method_id, spent_on, "
        "source, created_at, updated_at) VALUES(25000,1,1,'2026-05-10','manual',?,?)",
        (now().isoformat(), now().isoformat()),
    )
    fake_llm.response = "En mayo gastaste 25.000 pesos."
    await run_summary("2026-05")

    assert fake_llm.timeouts
    for timeout in fake_llm.timeouts:
        assert 0 < timeout <= settings.llm_timeout_summary_s


def test_migrations_are_idempotent(db):
    from autonomos.db.connection import init_db, schema_version

    before = db.execute("SELECT COUNT(*) c FROM categories").fetchone()["c"]
    db_connection.reset_for_tests()
    init_db()
    conn = get_db()
    assert conn.execute("SELECT COUNT(*) c FROM categories").fetchone()["c"] == before
    assert (
        int(conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0])
        == schema_version()
    )
