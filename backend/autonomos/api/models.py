"""Typed request/response models mirroring the Interface Contract.

These exist so `/openapi.json` is a real integration aid for a frontend
implementer who cannot see this code (KD-3, R10). Where this file and the design
document disagree, the design document wins.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

Source = Literal["manual", "voice"]
Resolution = Literal["rules", "llm", "none"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="ignore")


# --- errors ---------------------------------------------------------------


class ErrorField(Strict):
    field: str
    reason: str


class ErrorBody(Strict):
    code: str
    message: str
    fields: list[ErrorField] | None = None
    details: dict[str, Any] = {}


class ErrorEnvelope(Strict):
    error: ErrorBody


# --- health ---------------------------------------------------------------


class Origins(Strict):
    """Absolute origins (scheme + host + port, no trailing path).

    `null` means "that origin is not configured" — and for `lan`, that the
    fallback listener is disabled. A client must read that as "no alternative
    exists", not as an error.
    """

    primary: str | None = None
    lan: str | None = None


class Health(Strict):
    status: str
    server_time: str
    tz: str
    version: str
    origins: Origins


class Status(Strict):
    transcription: Literal["ok", "unavailable"]
    llm: Literal["ok", "unavailable"]
    checked_at: str


# --- categories / payment methods ----------------------------------------


class LookupItem(Strict):
    id: int
    name: str
    sort_order: int
    archived: bool
    in_use_count: int


class LookupList(Strict):
    items: list[LookupItem]


class LookupCreate(Strict):
    name: str | None = None


class ArchiveResult(Strict):
    archived: bool
    affected_expenses: int


# --- expenses -------------------------------------------------------------


class Expense(Strict):
    id: int
    amount_cop: int
    category_id: int
    category_name: str
    payment_method_id: int
    payment_method_name: str
    spent_on: str
    description: str | None
    created_at: str
    updated_at: str


class ExpenseList(Strict):
    items: list[Expense]
    total_count: int


class ExpenseCreate(Strict):
    amount_cop: int | None = None
    category_id: int | None = None
    payment_method_id: int | None = None
    spent_on: str | None = None
    description: str | None = None
    source: Source = "manual"


class ExpensePatch(Strict):
    amount_cop: int | None = None
    category_id: int | None = None
    payment_method_id: int | None = None
    spent_on: str | None = None
    description: str | None = None


class CategoryBreakdown(Strict):
    category_id: int
    name: str
    amount_cop: int
    percent: int


class MethodBreakdown(Strict):
    payment_method_id: int
    name: str
    amount_cop: int


class DaySummary(Strict):
    date: str
    total_cop: int
    expense_count: int
    items: list[Expense]


class MonthSummary(Strict):
    month: str
    total_cop: int
    expense_count: int
    is_empty: bool
    by_category: list[CategoryBreakdown]
    by_payment_method: list[MethodBreakdown]


# --- journal --------------------------------------------------------------


class JournalEntry(Strict):
    id: int
    text: str
    written_at: str
    created_at: str
    updated_at: str


class JournalList(Strict):
    items: list[JournalEntry]
    next_before: str | None


class JournalCreate(Strict):
    text: str | None = None
    source: Source = "manual"


class JournalPatch(Strict):
    text: str | None = None


# --- voice / parsing ------------------------------------------------------


class ResolvedBy(Strict):
    amount: Resolution
    category: Resolution
    payment_method: Resolution


class ExpenseDraft(Strict):
    amount_cop: int | None
    category_id: int | None
    category_name: str | None
    payment_method_id: int | None
    payment_method_name: str | None
    description: str
    description_truncated: bool
    resolved_by: ResolvedBy


class TranscribeResponse(Strict):
    transcript: str
    audio_ms: int
    elapsed_ms: int
    draft: ExpenseDraft | None


class TextRequest(Strict):
    text: str = ""


class SuggestCategoryResponse(Strict):
    category_id: int | None
    category_name: str | None
    source: Resolution


# --- insights -------------------------------------------------------------


class QuestionCreate(Strict):
    question: str | None = None
    source: Literal["text", "voice"] = "text"


class QuestionAccepted(Strict):
    job_id: str
    status: Literal["queued"]
    created_at: str


class Facts(Strict):
    period_label: str
    period_start: str
    period_end: str
    period_assumed: bool
    domain: Literal["finances", "journal", "both"]
    total_cop: int | None = None
    expense_count: int | None = None
    by_category: list[dict[str, Any]] | None = None
    journal_entries_considered: int | None = None
    journal_entries_used: int | None = None
    journal_truncated: bool = False


class JobStatus(Strict):
    job_id: str
    status: Literal["queued", "running", "done", "failed", "cancelled"]
    question: str
    # `elapsed_ms` is the only progress signal, and no completion fraction
    # exists or may be implied (KD-11).
    elapsed_ms: int
    # There is deliberately no `partial_answer` here. No LLM-generated text
    # reaches a client before NumericGuard has passed on the complete output:
    # a figure shown for forty seconds and then retracted was still shown, and
    # 11.2 says figures the user sees must match the Finances screen. The
    # column stays in `insight_jobs` for server-side diagnostics only.
    answer: str | None
    facts: Facts | None
    error_code: str | None
    created_at: str
    finished_at: str | None
