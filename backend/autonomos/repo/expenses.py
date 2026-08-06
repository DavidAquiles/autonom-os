"""Expense persistence and the day/month aggregations (Requirements 2, 4, 5).

`source` is stored and **never returned** — 9.5 and 10.4 require a voice-captured
record to be indistinguishable from a typed one, and a field present in a
response is a field a component will eventually display.
"""

from __future__ import annotations

import sqlite3

from ..clock import month_bounds, now_iso, parse_date, today_str
from ..errors import NotFound, ValidationError, field_error
from . import lookup

DESCRIPTION_MAX = 1000

_SELECT = """
SELECT e.id, e.amount_cop, e.category_id, c.name AS category_name,
       e.payment_method_id, p.name AS payment_method_name,
       e.spent_on, e.description, e.created_at, e.updated_at
FROM expenses e
JOIN categories c ON c.id = e.category_id
JOIN payment_methods p ON p.id = e.payment_method_id
"""


def row_to_expense(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "amount_cop": row["amount_cop"],
        "category_id": row["category_id"],
        "category_name": row["category_name"],
        "payment_method_id": row["payment_method_id"],
        "payment_method_name": row["payment_method_name"],
        "spent_on": row["spent_on"],
        "description": row["description"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _validate_amount(value, errors: list[dict], required: bool) -> int | None:
    if value is None:
        if required:
            errors.append(field_error("amount_cop", "required"))
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(field_error("amount_cop", "not_an_integer"))
        return None
    if value <= 0:
        errors.append(field_error("amount_cop", "must_be_positive"))
        return None
    return value


def _validate_fk(
    conn: sqlite3.Connection,
    table: lookup.Table,
    field: str,
    value,
    errors: list[dict],
    required: bool,
) -> int | None:
    if value is None:
        if required:
            errors.append(field_error(field, "required"))
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(field_error(field, "unknown_id"))
        return None
    if not lookup.exists(conn, table, value):
        errors.append(field_error(field, "unknown_id"))
        return None
    return value


def _validate_spent_on(value, errors: list[dict]) -> str | None:
    if value is None:
        return None
    parsed = parse_date(str(value))
    if parsed is None:
        errors.append(field_error("spent_on", "required"))
        return None
    if parsed.isoformat() > today_str():
        # A record of what happened, not a planner (A9, 2.7).
        errors.append(field_error("spent_on", "future_date"))
        return None
    return parsed.isoformat()


def _validate_description(value, errors: list[dict]) -> str | None:
    if value is None:
        return None
    text = str(value)
    if len(text) > DESCRIPTION_MAX:
        errors.append(field_error("description", "too_long"))
        return None
    return text


def create(conn: sqlite3.Connection, payload: dict) -> dict:
    errors: list[dict] = []
    amount = _validate_amount(payload.get("amount_cop"), errors, required=True)
    category_id = _validate_fk(
        conn, lookup.CATEGORIES, "category_id", payload.get("category_id"), errors, True
    )
    method_id = _validate_fk(
        conn,
        lookup.PAYMENT_METHODS,
        "payment_method_id",
        payload.get("payment_method_id"),
        errors,
        True,
    )
    spent_on = _validate_spent_on(payload.get("spent_on"), errors)
    description = _validate_description(payload.get("description"), errors)
    source = payload.get("source") or "manual"
    if source not in ("manual", "voice"):
        source = "manual"
    if errors:
        raise ValidationError(errors)

    ts = now_iso()
    cursor = conn.execute(
        """
        INSERT INTO expenses(amount_cop, category_id, payment_method_id, spent_on,
                             description, source, created_at, updated_at)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            amount,
            category_id,
            method_id,
            spent_on or today_str(),
            description,
            source,
            ts,
            ts,
        ),
    )
    return get(conn, int(cursor.lastrowid))


def get(conn: sqlite3.Connection, expense_id: int) -> dict:
    row = conn.execute(f"{_SELECT} WHERE e.id = ?", (expense_id,)).fetchone()
    if row is None:
        raise NotFound("expense")
    return row_to_expense(row)


def update(conn: sqlite3.Connection, expense_id: int, payload: dict) -> dict:
    if conn.execute("SELECT 1 FROM expenses WHERE id = ?", (expense_id,)).fetchone() is None:
        raise NotFound("expense")
    errors: list[dict] = []
    sets: list[str] = []
    values: list[object] = []

    if "amount_cop" in payload:
        amount = _validate_amount(payload["amount_cop"], errors, required=True)
        if amount is not None:
            sets.append("amount_cop = ?")
            values.append(amount)
    if "category_id" in payload:
        cid = _validate_fk(
            conn, lookup.CATEGORIES, "category_id", payload["category_id"], errors, True
        )
        if cid is not None:
            sets.append("category_id = ?")
            values.append(cid)
    if "payment_method_id" in payload:
        mid = _validate_fk(
            conn,
            lookup.PAYMENT_METHODS,
            "payment_method_id",
            payload["payment_method_id"],
            errors,
            True,
        )
        if mid is not None:
            sets.append("payment_method_id = ?")
            values.append(mid)
    if "spent_on" in payload:
        if payload["spent_on"] is None:
            errors.append(field_error("spent_on", "required"))
        else:
            spent_on = _validate_spent_on(payload["spent_on"], errors)
            if spent_on is not None:
                sets.append("spent_on = ?")
                values.append(spent_on)
    if "description" in payload:
        description = _validate_description(payload["description"], errors)
        if not errors:
            sets.append("description = ?")
            values.append(description)

    if errors:
        raise ValidationError(errors)
    if sets:
        sets.append("updated_at = ?")
        values.append(now_iso())
        values.append(expense_id)
        conn.execute(f"UPDATE expenses SET {', '.join(sets)} WHERE id = ?", values)
    return get(conn, expense_id)


def delete(conn: sqlite3.Connection, expense_id: int) -> None:
    cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    if cursor.rowcount == 0:
        raise NotFound("expense")


def list_expenses(
    conn: sqlite3.Connection,
    *,
    date: str | None = None,
    month: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[dict], int]:
    where = ""
    params: list[object] = []
    if date:
        where = "WHERE e.spent_on = ?"
        params.append(date)
    elif month:
        start, end = month_bounds(month)
        where = "WHERE e.spent_on BETWEEN ? AND ?"
        params.extend([start, end])

    total = conn.execute(
        f"SELECT COUNT(*) AS c FROM expenses e {where.replace('e.', 'e.')}", params
    ).fetchone()["c"]
    rows = conn.execute(
        f"{_SELECT} {where} ORDER BY e.spent_on DESC, e.created_at DESC, e.id DESC "
        "LIMIT ? OFFSET ?",
        (*params, limit, offset),
    ).fetchall()
    return [row_to_expense(row) for row in rows], int(total)


def day_summary(conn: sqlite3.Connection, date: str) -> dict:
    items, _count = list_expenses(conn, date=date, limit=500, offset=0)
    total = sum(item["amount_cop"] for item in items)
    return {
        "date": date,
        "total_cop": total,
        "expense_count": len(items),
        "items": items,
    }


def largest_remainder_percents(amounts: list[int], total: int) -> list[int]:
    """Integer percentages that sum to exactly 100 when `total > 0` (4.3)."""
    if total <= 0 or not amounts:
        return [0] * len(amounts)
    exact = [amount * 100 / total for amount in amounts]
    floors = [int(value) for value in exact]
    shortfall = 100 - sum(floors)
    order = sorted(
        range(len(amounts)),
        key=lambda i: (-(exact[i] - floors[i]), -amounts[i], i),
    )
    for k in range(max(0, shortfall)):
        floors[order[k % len(order)]] += 1
    return floors


def month_summary(conn: sqlite3.Connection, month: str) -> dict:
    start, end = month_bounds(month)
    totals = conn.execute(
        "SELECT COALESCE(SUM(amount_cop), 0) AS total, COUNT(*) AS n "
        "FROM expenses WHERE spent_on BETWEEN ? AND ?",
        (start, end),
    ).fetchone()
    total = int(totals["total"])
    count = int(totals["n"])
    if count == 0:
        # A plain empty state, never a zeroed chart (4.5).
        return {
            "month": month,
            "total_cop": 0,
            "expense_count": 0,
            "is_empty": True,
            "by_category": [],
            "by_payment_method": [],
        }

    category_rows = conn.execute(
        """
        SELECT e.category_id AS id, c.name AS name, SUM(e.amount_cop) AS amount
        FROM expenses e JOIN categories c ON c.id = e.category_id
        WHERE e.spent_on BETWEEN ? AND ?
        GROUP BY e.category_id, c.name
        ORDER BY amount DESC, c.name ASC
        """,
        (start, end),
    ).fetchall()
    amounts = [int(row["amount"]) for row in category_rows]
    percents = largest_remainder_percents(amounts, total)
    by_category = [
        {
            "category_id": row["id"],
            "name": row["name"],
            "amount_cop": int(row["amount"]),
            "percent": percents[i],
        }
        for i, row in enumerate(category_rows)
    ]

    method_rows = conn.execute(
        """
        SELECT e.payment_method_id AS id, p.name AS name, SUM(e.amount_cop) AS amount
        FROM expenses e JOIN payment_methods p ON p.id = e.payment_method_id
        WHERE e.spent_on BETWEEN ? AND ?
        GROUP BY e.payment_method_id, p.name
        ORDER BY amount DESC, p.name ASC
        """,
        (start, end),
    ).fetchall()
    by_payment_method = [
        {
            "payment_method_id": row["id"],
            "name": row["name"],
            "amount_cop": int(row["amount"]),
        }
        for row in method_rows
    ]

    return {
        "month": month,
        "total_cop": total,
        "expense_count": count,
        "is_empty": False,
        "by_category": by_category,
        "by_payment_method": by_payment_method,
    }


def first_expense_date(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT MIN(spent_on) AS d FROM expenses").fetchone()
    return row["d"] if row and row["d"] else None
