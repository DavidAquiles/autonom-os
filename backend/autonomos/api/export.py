"""`GET /api/export` — the only export endpoint (14.2).

CSV exports were cut at the Approve Plan gate on 2026-08-05: the JSON dump
satisfies 14.2 on its own and each CSV would have held only half the data.
`expenses.csv` and `journal.csv` do not exist and must not be added.

This is the one place `source` is emitted: an archival dump is not a rendered
list, so 9.5/10.4 are unaffected.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Response

from ..clock import now_iso, today_str
from ..db import get_db
from ..db.connection import schema_version

router = APIRouter()


def build_export() -> dict:
    conn = get_db()

    def rows(sql: str) -> list[dict]:
        return [dict(row) for row in conn.execute(sql).fetchall()]

    return {
        "exported_at": now_iso(),
        "schema_version": schema_version(),
        "categories": rows(
            "SELECT id, name, sort_order, archived_at, created_at FROM categories "
            "ORDER BY sort_order, id"
        ),
        "payment_methods": rows(
            "SELECT id, name, sort_order, archived_at, created_at FROM payment_methods "
            "ORDER BY sort_order, id"
        ),
        # ids *and* names, so the file is readable in any text editor with no
        # reference to this app.
        "expenses": rows(
            """
            SELECT e.id, e.amount_cop, e.category_id, c.name AS category_name,
                   e.payment_method_id, p.name AS payment_method_name,
                   e.spent_on, e.description, e.source, e.created_at, e.updated_at
            FROM expenses e
            JOIN categories c ON c.id = e.category_id
            JOIN payment_methods p ON p.id = e.payment_method_id
            ORDER BY e.spent_on, e.id
            """
        ),
        "journal_entries": rows(
            "SELECT id, text, written_at, source, created_at, updated_at "
            "FROM journal_entries ORDER BY written_at, id"
        ),
        "summaries": rows(
            "SELECT id, period_kind, period_key, status, text, model, generated_at, "
            "attempts, created_at FROM summaries ORDER BY period_key"
        ),
    }


@router.get("")
def export_all() -> Response:
    payload = json.dumps(build_export(), ensure_ascii=False, indent=2)
    filename = f"autonomos-{today_str()}.json"
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
