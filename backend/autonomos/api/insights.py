"""`/api/insights/*` — questions as polled jobs (KD-11) and the stored summary.

Insights are strictly read-only: no handler on this path writes to `expenses` or
`journal_entries` (11.6, A17).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Response

from ..clock import month_label_es, now
from ..db import get_db
from ..errors import ApiError, NotFound, ValidationError, field_error
from ..insights import runner
from ..repo import jobs as jobs_repo
from ..repo import summaries as summaries_repo
from .health import current_status
from .models import JobStatus, QuestionAccepted, QuestionCreate

log = logging.getLogger("autonomos.api.insights")

router = APIRouter()

QUESTION_MAX = 500


@router.post("/questions", response_model=QuestionAccepted, status_code=202)
async def ask(payload: QuestionCreate) -> dict:
    question = (payload.question or "").strip()
    if not question:
        raise ValidationError([field_error("question", "blank")])
    if len(question) > QUESTION_MAX:
        raise ValidationError([field_error("question", "too_long")])

    status = await current_status()
    if status["llm"] != "ok":
        raise ApiError(503, "llm_unavailable", "the local model is not answering")

    conn = get_db()
    # A22 allows one question at a time, so a second is rejected rather than
    # queued — the only condition that emits `busy` (KD-11).
    if jobs_repo.active_job(conn) is not None:
        raise ApiError(409, "busy", "a question is already queued or running")

    row = jobs_repo.create(conn, question, payload.source)
    runner.start_question(row["id"], question)
    return {"job_id": row["id"], "status": "queued", "created_at": row["created_at"]}


def _elapsed_ms(row) -> int:
    started = datetime.fromisoformat(row["created_at"])
    end = datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else now()
    return max(0, int((end - started).total_seconds() * 1000))


@router.get("/questions/{job_id}", response_model=JobStatus)
def job_status(job_id: str) -> dict:
    row = jobs_repo.get(get_db(), job_id)
    return {
        "job_id": row["id"],
        "status": row["status"],
        "question": row["question"],
        "elapsed_ms": _elapsed_ms(row),
        # `partial_answer` is NOT serialised (KD-11). It holds text NumericGuard
        # has not yet run on; `answer` stays null until the job is `done`.
        "answer": row["answer"],
        "facts": json.loads(row["facts_json"]) if row["facts_json"] else None,
        "error_code": row["error_code"],
        "created_at": row["created_at"],
        "finished_at": row["finished_at"],
    }


@router.delete("/questions/{job_id}", status_code=204)
def cancel_job(job_id: str) -> Response:
    conn = get_db()
    row = jobs_repo.find(conn, job_id)
    if row is None:
        raise NotFound("insight job")
    runner.registry.cancel(job_id)
    if row["status"] in jobs_repo.ACTIVE_STATUSES:
        jobs_repo.finish_cancelled(conn, job_id)
    # Saved data is untouched — there was never anything to touch (11.13).
    return Response(status_code=204)


@router.get("/summaries/latest")
def latest_summary() -> dict:
    """Reads a stored row; never triggers generation (11.15). Always instant.

    A finished row (`ready`/`empty`) is preferred over a newer in-flight one, so
    a readable summary is never hidden behind a month currently being produced.
    """
    conn = get_db()
    row = summaries_repo.latest_ready(conn) or summaries_repo.latest(conn)
    if row is None:
        return {"status": "none"}  # 11.16

    period_key = row["period_key"]
    label = month_label_es(period_key)
    status = row["status"]
    if status == "ready":
        return {
            "status": "ready",
            "period_kind": row["period_kind"],
            "period_key": period_key,
            "period_label": label,
            "text": row["text"],
            "generated_at": row["generated_at"],
            "model": row["model"],
            "facts": json.loads(row["facts_json"]) if row["facts_json"] else None,
        }
    if status == "generating":
        return {
            "status": "generating",
            "period_key": period_key,
            "period_label": label,
            "started_at": row["last_attempt_at"] or row["created_at"],
        }
    if status == "empty":
        return {"status": "empty", "period_key": period_key, "period_label": label}
    return {
        "status": "failed",
        "period_key": period_key,
        "error_code": row["error_code"] or "internal",
    }
