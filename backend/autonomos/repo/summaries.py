"""Monthly summary rows (KD-12).

There is no `pending` status: a completed month that should have a summary and
has **no row** *is* pending, which is what the catch-up scan looks for. A
cancelled or crash-orphaned run deletes its row rather than sitting at
`generating` forever; only genuine failures persist, and only three times.
"""

from __future__ import annotations

import json
import sqlite3

from ..clock import now_iso


def get(conn: sqlite3.Connection, period_key: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM summaries WHERE period_key = ?", (period_key,)
    ).fetchone()


def latest(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """The most recent row by period, whatever its status.

    `GET /latest` reads this and never triggers generation (11.15).
    """
    return conn.execute(
        "SELECT * FROM summaries ORDER BY period_key DESC LIMIT 1"
    ).fetchone()


def latest_ready(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """The most recent month that actually has a written summary.

    `empty` is deliberately **not** included. An `empty` row records that a
    month had nothing in it; it is not a summary, and treating it as one let a
    single unused month permanently hide the last real summary (QA D3, 11.15).
    """
    return conn.execute(
        "SELECT * FROM summaries WHERE status = 'ready' ORDER BY period_key DESC LIMIT 1"
    ).fetchone()


def start(conn: sqlite3.Connection, period_key: str) -> None:
    ts = now_iso()
    existing = get(conn, period_key)
    if existing is None:
        conn.execute(
            "INSERT INTO summaries(period_kind, period_key, status, attempts, "
            "last_attempt_at, created_at) VALUES('month', ?, 'generating', 1, ?, ?)",
            (period_key, ts, ts),
        )
    else:
        conn.execute(
            "UPDATE summaries SET status='generating', attempts = attempts + 1, "
            "last_attempt_at = ?, error_code = NULL WHERE period_key = ?",
            (ts, period_key),
        )


def finish_ready(
    conn: sqlite3.Connection, period_key: str, text: str, facts: dict, model: str
) -> None:
    conn.execute(
        "UPDATE summaries SET status='ready', text=?, facts_json=?, model=?, "
        "generated_at=?, error_code=NULL WHERE period_key = ?",
        (text, json.dumps(facts, ensure_ascii=False), model, now_iso(), period_key),
    )


def finish_empty(conn: sqlite3.Connection, period_key: str) -> None:
    conn.execute(
        "UPDATE summaries SET status='empty', text=NULL, facts_json=NULL, "
        "generated_at=?, error_code=NULL WHERE period_key = ?",
        (now_iso(), period_key),
    )


def finish_failed(conn: sqlite3.Connection, period_key: str, error_code: str) -> None:
    conn.execute(
        "UPDATE summaries SET status='failed', error_code=?, generated_at=NULL "
        "WHERE period_key = ?",
        (error_code, period_key),
    )


def drop(conn: sqlite3.Connection, period_key: str) -> None:
    """A cancelled run deletes its row, returning the month to 'pending'."""
    conn.execute("DELETE FROM summaries WHERE period_key = ?", (period_key,))


def delete_orphaned_generating(conn: sqlite3.Connection) -> int:
    """Startup sweep: the arbiter is in-process, so nothing survives a restart.

    A row left at `generating` by a crash is indistinguishable from a
    cancellation and is treated identically (KD-12).
    """
    cursor = conn.execute("DELETE FROM summaries WHERE status = 'generating'")
    return cursor.rowcount


def months_needing_summary(
    conn: sqlite3.Connection, candidate_months: list[str], max_attempts: int
) -> list[str]:
    """"Lacks a finished summary" — no row, or `failed` with attempts < max."""
    rows = {
        row["period_key"]: row
        for row in conn.execute("SELECT * FROM summaries").fetchall()
    }
    needed = []
    for month in candidate_months:
        row = rows.get(month)
        if row is None:
            needed.append(month)
        elif row["status"] == "failed" and int(row["attempts"]) < max_attempts:
            needed.append(month)
    return needed


def attempts_for(conn: sqlite3.Connection, period_key: str) -> int:
    row = get(conn, period_key)
    return int(row["attempts"]) if row else 0
