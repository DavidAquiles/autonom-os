"""Journal persistence (Requirements 6, 7).

Text is stored byte-exact — line breaks, blank lines, accents, ñ, ¿ and ¡ all
survive the round trip, and there is no truncation at any length (6.4-6.7).
Each submission is a new row; nothing merges (6.3). `source` is never returned.
"""

from __future__ import annotations

import sqlite3

from ..clock import now_iso
from ..errors import NotFound, ValidationError, field_error


def row_to_entry(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "text": row["text"],
        "written_at": row["written_at"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _validate_text(value) -> str:
    if value is None or not isinstance(value, str) or not value.strip():
        raise ValidationError([field_error("text", "blank")])
    return value  # stored exactly as sent; only the blank check trims


def create(conn: sqlite3.Connection, payload: dict) -> dict:
    text = _validate_text(payload.get("text"))
    source = payload.get("source") or "manual"
    if source not in ("manual", "voice"):
        source = "manual"
    ts = now_iso()
    cursor = conn.execute(
        "INSERT INTO journal_entries(text, written_at, source, created_at, updated_at) "
        "VALUES(?,?,?,?,?)",
        (text, ts, source, ts, ts),
    )
    return get(conn, int(cursor.lastrowid))


def get(conn: sqlite3.Connection, entry_id: int) -> dict:
    row = conn.execute("SELECT * FROM journal_entries WHERE id = ?", (entry_id,)).fetchone()
    if row is None:
        raise NotFound("journal entry")
    return row_to_entry(row)


def update(conn: sqlite3.Connection, entry_id: int, payload: dict) -> dict:
    if (
        conn.execute("SELECT 1 FROM journal_entries WHERE id = ?", (entry_id,)).fetchone()
        is None
    ):
        raise NotFound("journal entry")
    text = _validate_text(payload.get("text"))
    conn.execute(
        "UPDATE journal_entries SET text = ?, updated_at = ? WHERE id = ?",
        (text, now_iso(), entry_id),
    )
    return get(conn, entry_id)


def delete(conn: sqlite3.Connection, entry_id: int) -> None:
    cursor = conn.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
    if cursor.rowcount == 0:
        raise NotFound("journal entry")


def list_entries(
    conn: sqlite3.Connection,
    *,
    date: str | None = None,
    before: str | None = None,
    limit: int = 50,
) -> tuple[list[dict], str | None]:
    where = ""
    params: list[object] = []
    if date:
        where = "WHERE substr(written_at, 1, 10) = ?"
        params.append(date)
    elif before:
        where = "WHERE written_at < ?"
        params.append(before)
    rows = conn.execute(
        f"SELECT * FROM journal_entries {where} ORDER BY written_at DESC, id DESC LIMIT ?",
        (*params, limit + 1),
    ).fetchall()
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [row_to_entry(row) for row in rows]
    next_before = items[-1]["written_at"] if (has_more and items) else None
    return items, next_before


def entries_in_range(
    conn: sqlite3.Connection, start_date: str, end_date: str, *, oldest_first: bool = False
) -> list[dict]:
    """Entries whose *local* day falls inside [start_date, end_date]."""
    order = "ASC" if oldest_first else "DESC"
    rows = conn.execute(
        f"""
        SELECT * FROM journal_entries
        WHERE substr(written_at, 1, 10) BETWEEN ? AND ?
        ORDER BY written_at {order}, id {order}
        """,
        (start_date, end_date),
    ).fetchall()
    return [row_to_entry(row) for row in rows]


def count_in_range(conn: sqlite3.Connection, start_date: str, end_date: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM journal_entries "
        "WHERE substr(written_at, 1, 10) BETWEEN ? AND ?",
        (start_date, end_date),
    ).fetchone()
    return int(row["c"])


def first_entry_date(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT MIN(written_at) AS d FROM journal_entries").fetchone()
    return row["d"][:10] if row and row["d"] else None
