"""Categories and payment methods — identical in every respect (Interface Contract).

Nothing is ever hard-deleted: a removal is an archive (3.4), so an expense can
never be orphaned and a historical view always resolves the name it was filed
under.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from ..clock import now_iso
from ..errors import Conflict, InUse, NotFound, ValidationError, field_error
from ..parsing.text import normalize

NAME_MAX = 40


@dataclass(frozen=True)
class Table:
    name: str
    fk_column: str
    what: str


CATEGORIES = Table("categories", "category_id", "category")
PAYMENT_METHODS = Table("payment_methods", "payment_method_id", "payment method")


def validate_name(raw: str | None) -> str:
    name = (raw or "").strip()
    if not name:
        raise ValidationError([field_error("name", "blank")])
    if len(name) > NAME_MAX:
        raise ValidationError([field_error("name", "too_long")])
    return name


def _row_to_item(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "sort_order": row["sort_order"],
        "archived": row["archived_at"] is not None,
        "in_use_count": row["in_use_count"],
    }


def list_items(conn: sqlite3.Connection, table: Table, include_archived: bool) -> list[dict]:
    where = "" if include_archived else "WHERE t.archived_at IS NULL"
    rows = conn.execute(
        f"""
        SELECT t.id, t.name, t.sort_order, t.archived_at,
               (SELECT COUNT(*) FROM expenses e WHERE e.{table.fk_column} = t.id) AS in_use_count
        FROM {table.name} t
        {where}
        ORDER BY t.sort_order, t.id
        """
    ).fetchall()
    return [_row_to_item(row) for row in rows]


def get_item(conn: sqlite3.Connection, table: Table, item_id: int) -> dict:
    row = conn.execute(
        f"""
        SELECT t.id, t.name, t.sort_order, t.archived_at,
               (SELECT COUNT(*) FROM expenses e WHERE e.{table.fk_column} = t.id) AS in_use_count
        FROM {table.name} t WHERE t.id = ?
        """,
        (item_id,),
    ).fetchone()
    if row is None:
        raise NotFound(table.what)
    return _row_to_item(row)


def _find_by_normalized_name(
    conn: sqlite3.Connection, table: Table, name: str, archived: bool | None
) -> sqlite3.Row | None:
    target = normalize(name)
    rows = conn.execute(f"SELECT * FROM {table.name}").fetchall()
    for row in rows:
        if normalize(row["name"]) != target:
            continue
        is_archived = row["archived_at"] is not None
        if archived is None or is_archived == archived:
            return row
    return None


def create_item(conn: sqlite3.Connection, table: Table, raw_name: str) -> tuple[dict, int]:
    """Create, or un-archive a matching archived row (Interface Contract).

    Returns `(item, status_code)` — 201 for a new row, 200 for an un-archive.
    """
    name = validate_name(raw_name)
    if _find_by_normalized_name(conn, table, name, archived=False) is not None:
        raise Conflict(f"an active {table.what} already has that name")

    archived_row = _find_by_normalized_name(conn, table, name, archived=True)
    if archived_row is not None:
        conn.execute(
            f"UPDATE {table.name} SET archived_at = NULL, name = ? WHERE id = ?",
            (name, archived_row["id"]),
        )
        return get_item(conn, table, archived_row["id"]), 200

    next_order = conn.execute(
        f"SELECT COALESCE(MAX(sort_order), -1) + 1 AS n FROM {table.name}"
    ).fetchone()["n"]
    cursor = conn.execute(
        f"INSERT INTO {table.name}(name, sort_order, created_at) VALUES(?,?,?)",
        (name, next_order, now_iso()),
    )
    return get_item(conn, table, int(cursor.lastrowid)), 201


def rename_item(conn: sqlite3.Connection, table: Table, item_id: int, raw_name: str) -> dict:
    name = validate_name(raw_name)
    existing = conn.execute(
        f"SELECT id FROM {table.name} WHERE id = ?", (item_id,)
    ).fetchone()
    if existing is None:
        raise NotFound(table.what)
    clash = _find_by_normalized_name(conn, table, name, archived=False)
    if clash is not None and clash["id"] != item_id:
        raise Conflict(f"an active {table.what} already has that name")
    conn.execute(f"UPDATE {table.name} SET name = ? WHERE id = ?", (name, item_id))
    # Expenses reference the id, so every existing expense shows the new name
    # with no backfill (3.3).
    return get_item(conn, table, item_id)


def in_use_count(conn: sqlite3.Connection, table: Table, item_id: int) -> int:
    row = conn.execute(
        f"SELECT COUNT(*) AS c FROM expenses WHERE {table.fk_column} = ?", (item_id,)
    ).fetchone()
    return int(row["c"])


def archive_item(
    conn: sqlite3.Connection, table: Table, item_id: int, confirm: bool
) -> dict:
    row = conn.execute(f"SELECT * FROM {table.name} WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise NotFound(table.what)
    affected = in_use_count(conn, table, item_id)
    if affected > 0 and not confirm:
        raise InUse(affected)
    if row["archived_at"] is None:
        conn.execute(
            f"UPDATE {table.name} SET archived_at = ? WHERE id = ?", (now_iso(), item_id)
        )
    return {"archived": True, "affected_expenses": affected}


def active_ids(conn: sqlite3.Connection, table: Table) -> set[int]:
    return {
        row["id"]
        for row in conn.execute(
            f"SELECT id FROM {table.name} WHERE archived_at IS NULL"
        ).fetchall()
    }


def is_archived(conn: sqlite3.Connection, table: Table, item_id: int) -> bool:
    row = conn.execute(
        f"SELECT archived_at FROM {table.name} WHERE id = ?", (item_id,)
    ).fetchone()
    return bool(row and row["archived_at"] is not None)


def exists(conn: sqlite3.Connection, table: Table, item_id: int) -> bool:
    return (
        conn.execute(f"SELECT 1 FROM {table.name} WHERE id = ?", (item_id,)).fetchone()
        is not None
    )
