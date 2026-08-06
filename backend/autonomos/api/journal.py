"""`/api/journal` (Requirements 6, 7, 10.4)."""

from __future__ import annotations

from fastapi import APIRouter, Query, Response

from ..clock import parse_date
from ..db import get_db
from ..errors import ValidationError, field_error
from ..repo import journal as repo
from .models import JournalCreate, JournalEntry, JournalList, JournalPatch

router = APIRouter()


@router.post("", response_model=JournalEntry, status_code=201)
def create_entry(payload: JournalCreate) -> dict:
    return repo.create(get_db(), payload.model_dump())


@router.get("", response_model=JournalList)
def list_entries(
    date: str | None = Query(None),
    before: str | None = Query(None),
    limit: int = Query(50, ge=1, le=50),
) -> dict:
    if date is not None and parse_date(date) is None:
        raise ValidationError([field_error("date", "required")])
    items, next_before = repo.list_entries(
        get_db(), date=date, before=before, limit=limit
    )
    return {"items": items, "next_before": next_before}


@router.get("/{entry_id}", response_model=JournalEntry)
def get_entry(entry_id: int) -> dict:
    return repo.get(get_db(), entry_id)


@router.patch("/{entry_id}", response_model=JournalEntry)
def patch_entry(entry_id: int, payload: JournalPatch) -> dict:
    return repo.update(get_db(), entry_id, payload.model_dump(exclude_unset=True))


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int) -> Response:
    repo.delete(get_db(), entry_id)
    return Response(status_code=204)
