"""`/api/categories` and `/api/payment-methods` — identical in every respect.

Interface Contract: "shapes identical to /api/categories in every respect,
including the un-archive-on-recreate behaviour and the `confirm` gate", so both
routers come from one factory rather than two hand-copied modules.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response

from ..db import get_db
from ..repo import lookup
from .models import ArchiveResult, LookupCreate, LookupItem, LookupList


def build_router(table: lookup.Table) -> APIRouter:
    router = APIRouter()

    @router.get("", response_model=LookupList)
    def list_items(include_archived: bool = Query(False)) -> dict:
        return {"items": lookup.list_items(get_db(), table, include_archived)}

    @router.post("", response_model=LookupItem, status_code=201)
    def create_item(payload: LookupCreate, response: Response) -> dict:
        item, status_code = lookup.create_item(get_db(), table, payload.name or "")
        response.status_code = status_code  # 200 when an archived row was revived
        return item

    @router.patch("/{item_id}", response_model=LookupItem)
    def rename_item(item_id: int, payload: LookupCreate) -> dict:
        return lookup.rename_item(get_db(), table, item_id, payload.name or "")

    @router.delete("/{item_id}", response_model=ArchiveResult)
    def archive_item(item_id: int, confirm: bool = Query(False)) -> dict:
        return lookup.archive_item(get_db(), table, item_id, confirm)

    return router


categories_router = build_router(lookup.CATEGORIES)
payment_methods_router = build_router(lookup.PAYMENT_METHODS)
