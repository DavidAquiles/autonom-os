"""Insight job rows (KD-11).

Jobs are persisted so one survives a page reload and David can re-attach to a
running answer (13.3).
"""

from __future__ import annotations

import json
import sqlite3
import uuid

from ..clock import now_iso
from ..errors import NotFound

ACTIVE_STATUSES = ("queued", "running")


def create(conn: sqlite3.Connection, question: str, source: str) -> sqlite3.Row:
    job_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO insight_jobs(id, question, source, status, created_at) "
        "VALUES(?,?,?,'queued',?)",
        (job_id, question, source if source in ("text", "voice") else "text", now_iso()),
    )
    return get(conn, job_id)


def get(conn: sqlite3.Connection, job_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM insight_jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise NotFound("insight job")
    return row


def find(conn: sqlite3.Connection, job_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM insight_jobs WHERE id = ?", (job_id,)).fetchone()


def active_job(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """The one `queued`/`running` job, if any — the only source of `409 busy`."""
    placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
    return conn.execute(
        f"SELECT * FROM insight_jobs WHERE status IN ({placeholders}) "
        "ORDER BY created_at DESC LIMIT 1",
        ACTIVE_STATUSES,
    ).fetchone()


def mark_running(conn: sqlite3.Connection, job_id: str, facts: dict | None) -> None:
    conn.execute(
        "UPDATE insight_jobs SET status='running', started_at=?, facts_json=? WHERE id=?",
        (
            now_iso(),
            json.dumps(facts, ensure_ascii=False) if facts is not None else None,
            job_id,
        ),
    )


def set_facts(conn: sqlite3.Connection, job_id: str, facts: dict) -> None:
    conn.execute(
        "UPDATE insight_jobs SET facts_json=? WHERE id=?",
        (json.dumps(facts, ensure_ascii=False), job_id),
    )


def set_partial(conn: sqlite3.Connection, job_id: str, partial: str) -> None:
    conn.execute(
        "UPDATE insight_jobs SET partial_answer=? WHERE id=?", (partial, job_id)
    )


def finish_done(conn: sqlite3.Connection, job_id: str, answer: str) -> None:
    conn.execute(
        "UPDATE insight_jobs SET status='done', answer=?, partial_answer=NULL, "
        "finished_at=? WHERE id=?",
        (answer, now_iso(), job_id),
    )


def finish_failed(conn: sqlite3.Connection, job_id: str, error_code: str) -> None:
    conn.execute(
        "UPDATE insight_jobs SET status='failed', error_code=?, finished_at=? WHERE id=?",
        (error_code, now_iso(), job_id),
    )


def finish_cancelled(conn: sqlite3.Connection, job_id: str) -> None:
    conn.execute(
        "UPDATE insight_jobs SET status='cancelled', finished_at=? WHERE id=?",
        (now_iso(), job_id),
    )


def sweep_orphans(conn: sqlite3.Connection) -> int:
    """Startup: a job cannot still be running across a restart (KD-12)."""
    placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
    cursor = conn.execute(
        f"UPDATE insight_jobs SET status='failed', error_code='internal', finished_at=? "
        f"WHERE status IN ({placeholders})",
        (now_iso(), *ACTIVE_STATUSES),
    )
    return cursor.rowcount
