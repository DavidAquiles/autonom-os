"""FastAPI routers. Contains no business logic (design: Backend modules)."""

from __future__ import annotations

from fastapi import APIRouter

from . import expenses, export, health, insights, journal, lookups, summary, voice

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(lookups.categories_router, prefix="/categories", tags=["categories"])
api_router.include_router(
    lookups.payment_methods_router, prefix="/payment-methods", tags=["payment-methods"]
)
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(summary.router, prefix="/summary", tags=["summary"])
api_router.include_router(journal.router, prefix="/journal", tags=["journal"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(export.router, prefix="/export", tags=["export"])

__all__ = ["api_router"]
