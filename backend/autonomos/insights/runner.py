"""The insight job runner: questions (KD-11) and monthly summaries (KD-12).

The four deterministic stages of KD-10 run *before* any generation — router,
facts, insufficiency pre-check — and NumericGuard runs after it. The answer
budget is a **deadline from `created_at`**, so time spent queueing behind a
transcription is subtracted from it rather than added to it, and a job that
cannot start with `LLM_MIN_START_BUDGET_S` left terminates rather than starting
generation it cannot finish.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime

from ..arbiter import (
    REASON_PREEMPTED,
    ArbiterTimeout,
    JobKind,
    Lease,
    get_arbiter,
)
from ..clock import month_bounds, month_label_es, now_iso
from ..config import get_settings
from ..db import get_db
from ..providers import (
    ProviderCancelled,
    ProviderTimeout,
    ProviderUnavailable,
    get_llm,
)
from ..repo import jobs as jobs_repo
from ..repo import summaries as summaries_repo
from . import guard, prompts
from .facts import FactSet, build_facts, range_has_data
from .router import PeriodUnrecognised, Route, route as route_question

log = logging.getLogger("autonomos.insights")

PARTIAL_FLUSH_S = 0.75


class _Registry:
    """In-process handles for running jobs, so `DELETE` can actually stop one."""

    def __init__(self) -> None:
        self.tasks: dict[str, asyncio.Task] = {}
        self.cancels: dict[str, asyncio.Event] = {}
        self.user_cancelled: set[str] = set()

    def register(self, job_id: str, task: asyncio.Task, cancel: asyncio.Event) -> None:
        self.tasks[job_id] = task
        self.cancels[job_id] = cancel

    def forget(self, job_id: str) -> None:
        self.tasks.pop(job_id, None)
        self.cancels.pop(job_id, None)
        self.user_cancelled.discard(job_id)

    def cancel(self, job_id: str) -> bool:
        event = self.cancels.get(job_id)
        if event is None:
            return False
        self.user_cancelled.add(job_id)
        event.set()
        return True


registry = _Registry()


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def start_question(job_id: str, question: str) -> None:
    """Fire the background task for a job row that already exists."""
    cancel = asyncio.Event()
    task = asyncio.ensure_future(_run_question(job_id, question, cancel))
    registry.register(job_id, task, cancel)
    task.add_done_callback(lambda _t: registry.forget(job_id))


async def _run_question(job_id: str, question: str, cancel: asyncio.Event) -> None:
    settings = get_settings()
    conn = get_db()
    arbiter = get_arbiter()
    started_wall = time.monotonic()

    try:
        row = jobs_repo.get(conn, job_id)
        deadline = (
            _parse_iso(row["created_at"]).timestamp() + settings.llm_deadline_answer_s
        )

        # --- stage 1: router (rules) ------------------------------------
        try:
            routed: Route = route_question(conn, question)
        except PeriodUnrecognised:
            jobs_repo.finish_failed(conn, job_id, "period_unrecognised")
            return

        # --- stage 3: insufficiency pre-check, before any model call ----
        if not range_has_data(conn, routed.period_start, routed.period_end):
            facts = build_facts(conn, routed, kind="question")
            jobs_repo.set_facts(conn, job_id, facts.to_wire())
            jobs_repo.finish_failed(conn, job_id, "insufficient_data")
            return

        # --- stage 2: facts (SQL computes) ------------------------------
        facts = build_facts(conn, routed, kind="question")
        jobs_repo.mark_running(conn, job_id, facts.to_wire())

        remaining = deadline - time.time()
        if remaining < settings.llm_min_start_budget_s:
            jobs_repo.finish_failed(conn, job_id, "llm_timeout")
            return

        wait_budget = max(0.0, remaining - settings.llm_min_start_budget_s)
        try:
            lease = await arbiter.acquire(
                JobKind.QUESTION, cancel, wait_timeout_s=wait_budget
            )
        except ArbiterTimeout:
            if job_id in registry.user_cancelled:
                jobs_repo.finish_cancelled(conn, job_id)
            else:
                jobs_repo.finish_failed(conn, job_id, "llm_timeout")
            return

        try:
            # The *deadline* is handed on, never a duration derived from it.
            # `_generate_answer` re-reads what is left before each attempt,
            # including the strict retry, so the whole job stays inside
            # `created_at + LLM_DEADLINE_ANSWER_S` (KD-11, AC 11.12).
            await _generate_answer(conn, job_id, question, facts, lease, deadline)
        finally:
            arbiter.release(lease)
    except Exception as exc:  # never leave a job row hanging
        log.exception("insight job %s failed: %s", job_id, exc)
        try:
            jobs_repo.finish_failed(get_db(), job_id, "internal")
        except Exception:
            pass
    finally:
        log.info(
            "insight job %s finished in %.1f s", job_id, time.monotonic() - started_wall
        )


async def _generate_answer(
    conn,
    job_id: str,
    question: str,
    facts: FactSet,
    lease: Lease,
    deadline: float,
) -> None:
    """Generate, guard, and at most one strict retry — all inside `deadline`.

    `deadline` is an **absolute** epoch time (`created_at + LLM_DEADLINE_ANSWER_S`),
    never a duration. Every attempt re-derives its own `timeout_s` from it, so a
    retry inherits what is actually left rather than a fresh allowance: a first
    generation that spends 76 s of the 110 s leaves the retry 34 s, not 110.
    """
    settings = get_settings()
    llm = get_llm()
    buffer: list[str] = []
    last_flush = 0.0

    def on_token(piece: str) -> None:
        """Accumulate, and checkpoint to `partial_answer` for diagnostics only.

        That column is **never serialised to a client** (KD-11): it holds text
        NumericGuard has not yet run on. It exists so a failed or preempted job
        can be inspected afterwards.
        """
        nonlocal last_flush
        buffer.append(piece)
        now = time.monotonic()
        if now - last_flush >= PARTIAL_FLUSH_S:
            last_flush = now
            try:
                jobs_repo.set_partial(conn, job_id, "".join(buffer))
            except Exception:  # diagnostics are never a failure path
                pass

    attempt = 0
    strict = False
    while True:
        attempt += 1
        buffer.clear()

        # Re-read the remaining budget before *every* attempt, the retry
        # included. The contract's `llm_timeout` covers both halves of this:
        # "the 110 s deadline from created_at elapsed, **or too little of it
        # remained to start**".
        remaining_s = deadline - time.time()
        if remaining_s < settings.llm_min_start_budget_s:
            log.info(
                "job %s: %.1fs left of its deadline on attempt %d, below the "
                "%.0fs floor — terminating rather than starting",
                job_id,
                remaining_s,
                attempt,
                settings.llm_min_start_budget_s,
            )
            jobs_repo.finish_failed(conn, job_id, "llm_timeout")
            return

        try:
            text = await llm.generate(
                prompts.answer_messages(question, facts, strict=strict),
                max_tokens=settings.llm_max_tokens_answer,
                # Nothing here wants creativity: the job is to restate stored
                # facts. Sampling variety is where the off-record clauses of
                # QA D2 came from.
                temperature=0.0,
                timeout_s=remaining_s,
                on_token=on_token,
                cancel=lease.cancel,
            )
        except ProviderCancelled:
            if lease.reason == REASON_PREEMPTED:
                # A voice capture took priority — a legitimate 11.12 outcome,
                # not a silent loss. The user re-asks; nothing restarts it.
                jobs_repo.finish_failed(conn, job_id, "preempted")
            elif job_id in registry.user_cancelled:
                jobs_repo.finish_cancelled(conn, job_id)
            else:
                jobs_repo.finish_failed(conn, job_id, "preempted")
            return
        except ProviderTimeout:
            jobs_repo.finish_failed(conn, job_id, "llm_timeout")
            return
        except ProviderUnavailable:
            jobs_repo.finish_failed(conn, job_id, "llm_unavailable")
            return

        if not text.strip():
            jobs_repo.finish_failed(conn, job_id, "internal")
            return

        # --- stage 4: NumericGuard --------------------------------------
        result = guard.check(text, facts)
        if result.ok:
            jobs_repo.finish_done(conn, job_id, text.strip())
            return
        log.warning("NumericGuard rejected %s: %s", job_id, result.offending)
        if attempt >= 2:
            jobs_repo.finish_failed(conn, job_id, "unverifiable_figures")
            return
        # Loop for one strict retry. Whether it can start at all is decided at
        # the top of the loop against the deadline, not against a decremented
        # duration — the retry gets the time that is left and nothing more.
        strict = True


# ---------------------------------------------------------------------------
# Monthly summaries (background class)
# ---------------------------------------------------------------------------


async def run_summary(period_key: str) -> str:
    """Generate one month's summary. Returns a terminal state name for logging.

    Cancellation by interactive work **deletes the row**, returning the month to
    the row-absent state the catch-up scan already handles, and burning no retry
    attempt (KD-12).
    """
    settings = get_settings()
    conn = get_db()
    arbiter = get_arbiter()
    cancel = asyncio.Event()
    start, end = month_bounds(period_key)
    routed = Route(
        period_start=start,
        period_end=end,
        period_label=month_label_es(period_key),
        period_assumed=False,
        domain="both",  # 11.14 requires spending **and** journal
    )

    if not range_has_data(conn, start, end):
        summaries_repo.start(conn, period_key)
        summaries_repo.finish_empty(conn, period_key)
        return "empty"

    facts = build_facts(conn, routed, kind="summary")

    try:
        lease = await arbiter.acquire(JobKind.SUMMARY, cancel)
    except ArbiterTimeout:
        return "not_started"

    summaries_repo.start(conn, period_key)
    llm = get_llm()
    try:
        attempt = 0
        strict = False
        while True:
            attempt += 1
            try:
                text = await llm.generate(
                    prompts.summary_messages(facts, strict=strict),
                    max_tokens=settings.llm_max_tokens_summary,
                    temperature=0.0,
                    timeout_s=settings.llm_timeout_summary_s,
                    cancel=lease.cancel,
                )
            except ProviderCancelled:
                summaries_repo.drop(conn, period_key)
                return "cancelled"
            except ProviderTimeout:
                summaries_repo.finish_failed(conn, period_key, "llm_timeout")
                return "failed"
            except ProviderUnavailable:
                summaries_repo.finish_failed(conn, period_key, "llm_unavailable")
                return "failed"

            if not text.strip():
                summaries_repo.finish_failed(conn, period_key, "internal")
                return "failed"

            result = guard.check(text, facts)
            if result.ok:
                summaries_repo.finish_ready(
                    conn, period_key, text.strip(), facts.to_wire(), settings.llm_model
                )
                return "ready"
            log.warning(
                "NumericGuard rejected summary %s: %s", period_key, result.offending
            )
            if attempt >= 2:
                summaries_repo.finish_failed(conn, period_key, "unverifiable_figures")
                return "failed"
            strict = True
    finally:
        arbiter.release(lease)


def sweep_on_startup() -> None:
    """Startup housekeeping (KD-12): nothing can still be generating."""
    conn = get_db()
    dropped = summaries_repo.delete_orphaned_generating(conn)
    orphaned_jobs = jobs_repo.sweep_orphans(conn)
    if dropped or orphaned_jobs:
        log.info(
            "startup sweep: %d orphaned summary rows deleted, %d jobs failed at %s",
            dropped,
            orphaned_jobs,
            now_iso(),
        )
