"""`/api/insights/*` end to end against fake sidecars (Requirement 11)."""

from __future__ import annotations

import time

from autonomos.clock import today
from autonomos.providers.base import ProviderUnavailable


def seed_expense(client, amount=14000, category_id=1):
    return client.post(
        "/api/expenses",
        json={
            "amount_cop": amount,
            "category_id": category_id,
            "payment_method_id": 1,
            "spent_on": today().isoformat(),
        },
    )


def poll(client, job_id, timeout_s=5.0):
    deadline = time.time() + timeout_s
    body = client.get(f"/api/insights/questions/{job_id}").json()
    while body["status"] in ("queued", "running") and time.time() < deadline:
        time.sleep(0.05)
        body = client.get(f"/api/insights/questions/{job_id}").json()
    return body


def test_11_12_a_question_is_accepted_immediately_with_a_job_id(client, fake_llm):
    seed_expense(client)
    fake_llm.response = "Gastaste 14.000 pesos este mes."
    started = time.monotonic()
    response = client.post(
        "/api/insights/questions", json={"question": "¿cuánto gasté este mes?", "source": "text"}
    )
    assert response.status_code == 202
    assert time.monotonic() - started < 1.0
    body = response.json()
    assert body["status"] == "queued"
    assert body["job_id"]


def test_11_2_no_unvalidated_text_is_ever_on_the_wire(client, fake_llm):
    """KD-11: `partial_answer` is not serialised and `answer` is null until
    `done`. NumericGuard runs on the *complete* output, so a figure shown
    mid-flight could be retracted afterwards — and one that was shown was still
    shown. The column stays for server-side diagnostics only."""
    from autonomos.db import get_db
    from autonomos.repo import jobs as jobs_repo

    seed_expense(client)
    fake_llm.delay_s = 2.0
    job = client.post(
        "/api/insights/questions", json={"question": "¿cuánto gasté hoy?"}
    ).json()
    time.sleep(0.3)

    in_flight = client.get(f"/api/insights/questions/{job['job_id']}").json()
    assert "partial_answer" not in in_flight
    assert in_flight["answer"] is None
    assert in_flight["status"] in ("queued", "running")
    assert in_flight["elapsed_ms"] >= 0  # the only progress signal

    client.delete(f"/api/insights/questions/{job['job_id']}")
    # The column itself still exists for diagnostics.
    assert "partial_answer" in jobs_repo.get(get_db(), job["job_id"]).keys()


def test_a_finished_job_still_carries_no_partial_field(client, fake_llm):
    seed_expense(client)
    fake_llm.response = "Hoy gastaste 14.000 pesos."
    job = client.post(
        "/api/insights/questions", json={"question": "¿cuánto gasté hoy?"}
    ).json()
    body = poll(client, job["job_id"])
    assert body["status"] == "done"
    assert "partial_answer" not in body
    assert body["answer"] == "Hoy gastaste 14.000 pesos."


def test_11_8_a_finance_question_is_answered_from_recorded_expenses(client, fake_llm):
    seed_expense(client, amount=14000)
    fake_llm.response = "Este mes gastaste 14.000 pesos, todo en Comida (100%)."
    job = client.post(
        "/api/insights/questions", json={"question": "¿cuánto gasté este mes?"}
    ).json()
    body = poll(client, job["job_id"])
    assert body["status"] == "done"
    assert body["answer"] == fake_llm.response
    assert body["facts"]["total_cop"] == 14000
    assert body["facts"]["period_assumed"] is False
    assert body["facts"]["by_category"][0]["percent"] == 100
    assert body["elapsed_ms"] >= 0


def test_11_9_a_journal_question_reports_the_two_counts(client, fake_llm):
    for i in range(3):
        client.post("/api/journal", json={"text": f"Hoy pensaba en la vida {i}"})
    fake_llm.response = "Escribiste sobre la vida."
    job = client.post(
        "/api/insights/questions", json={"question": "¿qué escribí en el diario este mes?"}
    ).json()
    body = poll(client, job["job_id"])
    assert body["status"] == "done"
    assert body["facts"]["domain"] == "journal"
    assert body["facts"]["journal_entries_considered"] == 3
    assert body["facts"]["journal_entries_used"] == 3
    assert body["facts"]["journal_truncated"] is False


def test_11_3_no_data_in_range_short_circuits_without_a_model_call(client, fake_llm):
    job = client.post(
        "/api/insights/questions", json={"question": "¿cuánto gasté el mes pasado?"}
    ).json()
    body = poll(client, job["job_id"])
    assert body["status"] == "failed"
    assert body["error_code"] == "insufficient_data"
    assert fake_llm.calls == []


def test_11_11_an_unresolvable_period_fails_explicitly(client, fake_llm):
    seed_expense(client)
    job = client.post(
        "/api/insights/questions",
        json={"question": "¿cuánto gasté en los últimos tres meses?"},
    ).json()
    body = poll(client, job["job_id"])
    assert body["status"] == "failed"
    assert body["error_code"] == "period_unrecognised"
    assert fake_llm.calls == []


def test_11_2_an_unverifiable_figure_is_retried_once_then_refused(client, fake_llm):
    seed_expense(client, amount=14000)
    fake_llm.response = "Gastaste 999.999 pesos este mes."
    job = client.post(
        "/api/insights/questions", json={"question": "¿cuánto gasté este mes?"}
    ).json()
    body = poll(client, job["job_id"])
    assert body["status"] == "failed"
    assert body["error_code"] == "unverifiable_figures"
    assert body["answer"] is None
    assert len(fake_llm.calls) == 2  # one retry with a stricter prompt


def test_a22_a_second_question_is_rejected_with_busy(client, fake_llm):
    seed_expense(client)
    fake_llm.delay_s = 2.0
    first = client.post("/api/insights/questions", json={"question": "¿cuánto gasté hoy?"})
    assert first.status_code == 202
    second = client.post("/api/insights/questions", json={"question": "¿y ayer?"})
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "busy"
    client.delete(f"/api/insights/questions/{first.json()['job_id']}")


def test_11_13_cancelling_stops_the_job_and_touches_no_data(client, fake_llm):
    expense = seed_expense(client).json()
    fake_llm.delay_s = 3.0
    job = client.post(
        "/api/insights/questions", json={"question": "¿cuánto gasté hoy?"}
    ).json()
    assert client.delete(f"/api/insights/questions/{job['job_id']}").status_code == 204
    body = client.get(f"/api/insights/questions/{job['job_id']}").json()
    assert body["status"] == "cancelled"
    assert client.get(f"/api/expenses/{expense['id']}").status_code == 200


def test_cancelling_an_unknown_job_is_not_found(client):
    assert client.delete("/api/insights/questions/nope").status_code == 404
    assert client.get("/api/insights/questions/nope").status_code == 404


def test_11_4_llm_unavailable_is_explicit_and_the_rest_keeps_working(client, fake_llm):
    from autonomos.api import health as health_api

    fake_llm.healthy = False
    health_api.invalidate_status_cache()
    response = client.post("/api/insights/questions", json={"question": "¿cuánto gasté?"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "llm_unavailable"
    # Capture and views are untouched by the model being down.
    assert seed_expense(client).status_code == 201
    assert client.get("/api/summary/day").json()["total_cop"] == 14000
    assert client.get("/api/status").json()["llm"] == "unavailable"


def test_provider_failure_during_generation_is_reported(client, fake_llm):
    seed_expense(client)
    fake_llm.raise_error = ProviderUnavailable("connection refused")
    job = client.post(
        "/api/insights/questions", json={"question": "¿cuánto gasté hoy?"}
    ).json()
    body = poll(client, job["job_id"])
    assert body["status"] == "failed"
    assert body["error_code"] == "llm_unavailable"


def test_blank_and_overlong_questions_are_validation_errors(client):
    blank = client.post("/api/insights/questions", json={"question": "  "})
    assert blank.status_code == 400
    assert {"field": "question", "reason": "blank"} in blank.json()["error"]["fields"]
    long = client.post("/api/insights/questions", json={"question": "x" * 501})
    assert {"field": "question", "reason": "too_long"} in long.json()["error"]["fields"]


def test_11_16_no_summary_ever_produced_is_an_explicit_state(client):
    assert client.get("/api/insights/summaries/latest").json() == {"status": "none"}


def test_11_15_and_11_18_a_stored_summary_is_returned_instantly(client, db):
    from autonomos.repo import summaries as summaries_repo

    facts = {"period_label": "julio de 2026", "domain": "both", "total_cop": 1000}
    summaries_repo.start(db, "2026-07")
    summaries_repo.finish_ready(db, "2026-07", "Resumen de julio.", facts, "modelo")

    started = time.monotonic()
    body = client.get("/api/insights/summaries/latest").json()
    assert time.monotonic() - started < 1.0
    assert body["status"] == "ready"
    assert body["period_key"] == "2026-07"
    assert body["period_label"] == "julio de 2026"
    assert body["text"] == "Resumen de julio."
    assert body["generated_at"]  # 11.18: says when it was produced
    assert body["facts"]["total_cop"] == 1000


def test_11_16_an_empty_period_is_its_own_state(client, db):
    from autonomos.repo import summaries as summaries_repo

    summaries_repo.start(db, "2026-06")
    summaries_repo.finish_empty(db, "2026-06")
    body = client.get("/api/insights/summaries/latest").json()
    assert body["status"] == "empty"
    assert body["period_key"] == "2026-06"


def test_a_failed_summary_is_reported_honestly(client, db):
    from autonomos.repo import summaries as summaries_repo

    summaries_repo.start(db, "2026-05")
    summaries_repo.finish_failed(db, "2026-05", "llm_timeout")
    body = client.get("/api/insights/summaries/latest").json()
    assert body["status"] == "failed"
    assert body["error_code"] == "llm_timeout"


def test_a_readable_summary_is_not_hidden_by_a_newer_generating_one(client, db):
    from autonomos.repo import summaries as summaries_repo

    summaries_repo.start(db, "2026-06")
    summaries_repo.finish_ready(db, "2026-06", "Resumen de junio.", {}, "modelo")
    summaries_repo.start(db, "2026-07")
    body = client.get("/api/insights/summaries/latest").json()
    assert body["status"] == "ready"
    assert body["period_key"] == "2026-06"
