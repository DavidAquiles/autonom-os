"""Restart durability (14.1) and the answer deadline arithmetic (KD-11)."""

from __future__ import annotations

import asyncio
from datetime import timedelta

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
