"""`/api/expenses`, the parser test seam, and the category assist (KD-8)."""

from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter, Query, Response

from ..arbiter import ArbiterTimeout, JobKind, get_arbiter
from ..clock import is_valid_month, parse_date
from ..config import get_settings
from ..db import get_db
from ..errors import ValidationError, field_error
from ..insights.prompts import category_assist_messages
from ..parsing.extractor import ExpenseDraftData, parse_expense_text
from ..parsing.text import normalize
from ..providers import get_llm
from ..repo import expenses as repo
from .models import (
    Expense,
    ExpenseCreate,
    ExpenseDraft,
    ExpenseList,
    ExpensePatch,
    SuggestCategoryResponse,
    TextRequest,
)

log = logging.getLogger("autonomos.api.expenses")

router = APIRouter()


def draft_to_wire(draft: ExpenseDraftData) -> dict:
    return {
        "amount_cop": draft.amount_cop,
        "category_id": draft.category_id,
        "category_name": draft.category_name,
        "payment_method_id": draft.payment_method_id,
        "payment_method_name": draft.payment_method_name,
        "description": draft.description,
        "description_truncated": draft.description_truncated,
        "resolved_by": dict(draft.resolved_by),
    }


@router.post("", response_model=Expense, status_code=201)
def create_expense(payload: ExpenseCreate) -> dict:
    return repo.create(get_db(), payload.model_dump(exclude_unset=False))


@router.get("", response_model=ExpenseList)
def list_expenses(
    date: str | None = Query(None),
    month: str | None = Query(None),
    limit: int = Query(200, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    if date is not None and parse_date(date) is None:
        raise ValidationError([field_error("date", "required")])
    if month is not None and not is_valid_month(month):
        raise ValidationError([field_error("month", "required")])
    items, total = repo.list_expenses(
        get_db(), date=date, month=month, limit=limit, offset=offset
    )
    return {"items": items, "total_count": total}


@router.post("/parse", response_model=ExpenseDraft)
def parse_expense(payload: TextRequest) -> dict:
    """Rule layer only, no model — the test seam behind 9.1/9.2/9.6/9.7.

    The frontend must not expose a typed natural-language expense path.
    """
    return draft_to_wire(parse_expense_text(get_db(), payload.text or ""))


@router.post("/suggest-category", response_model=SuggestCategoryResponse)
async def suggest_category(payload: TextRequest) -> dict:
    """Layer 2 of KD-8. Never fails the caller: a slow or absent model yields
    `{"category_id": null, "source": "none"}` with `200`."""
    settings = get_settings()
    received_at = time.monotonic()
    conn = get_db()
    text = (payload.text or "").strip()
    none_result = {"category_id": None, "category_name": None, "source": "none"}
    if not text:
        return none_result

    # The rules already know the answer more often than not, and cost nothing.
    draft = parse_expense_text(conn, text)
    if draft.category_id is not None:
        return {
            "category_id": draft.category_id,
            "category_name": draft.category_name,
            "source": "rules",
        }

    rows = conn.execute(
        "SELECT id, name FROM categories WHERE archived_at IS NULL ORDER BY sort_order, id"
    ).fetchall()
    names = [row["name"] for row in rows]
    if not names:
        return none_result

    cancel = asyncio.Event()
    arbiter = get_arbiter()
    remaining = settings.assist_timeout_s - (time.monotonic() - received_at)
    if remaining <= 0.5:
        return none_result
    try:
        lease = await arbiter.acquire(JobKind.ASSIST, cancel, wait_timeout_s=remaining)
    except ArbiterTimeout:
        # Category assist yields to everything; waiting simply produces the null
        # result it is already designed to produce (KD-12).
        return none_result

    try:
        remaining = settings.assist_timeout_s - (time.monotonic() - received_at)
        if remaining <= 0.5:
            return none_result
        answer = await get_llm().generate(
            category_assist_messages(text, names),
            max_tokens=settings.assist_max_tokens,
            temperature=0.0,
            timeout_s=remaining,
            cancel=lease.cancel,
        )
    except Exception as exc:
        log.info("category assist yielded nothing: %s", type(exc).__name__)
        return none_result
    finally:
        arbiter.release(lease)

    # Validated against the user's existing categories; anything else is
    # discarded and the field stays empty (9.3).
    wanted = normalize(answer)
    for row in rows:
        if normalize(row["name"]) == wanted:
            return {
                "category_id": row["id"],
                "category_name": row["name"],
                "source": "llm",
            }
    return none_result


@router.get("/{expense_id}", response_model=Expense)
def get_expense(expense_id: int) -> dict:
    return repo.get(get_db(), expense_id)


@router.patch("/{expense_id}", response_model=Expense)
def patch_expense(expense_id: int, payload: ExpensePatch) -> dict:
    return repo.update(get_db(), expense_id, payload.model_dump(exclude_unset=True))


@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: int) -> Response:
    repo.delete(get_db(), expense_id)
    return Response(status_code=204)
