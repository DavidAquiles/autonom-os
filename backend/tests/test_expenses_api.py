"""`/api/expenses` and `/api/summary/*` (Requirements 2, 3.5, 4, 5)."""

from __future__ import annotations

from datetime import timedelta

from autonomos.clock import today


def make_expense(client, **overrides):
    payload = {
        "amount_cop": 14000,
        "category_id": 1,
        "payment_method_id": 1,
    }
    payload.update(overrides)
    return client.post("/api/expenses", json=payload)


def test_2_1_saved_expense_is_dated_today_and_appears_in_the_day_total(client):
    response = make_expense(client)
    assert response.status_code == 201
    body = response.json()
    assert body["spent_on"] == today().isoformat()
    assert body["category_name"] == "Comida"

    day = client.get("/api/summary/day").json()
    assert day["total_cop"] == 14000
    assert day["expense_count"] == 1
    assert day["items"][0]["id"] == body["id"]


def test_source_is_never_returned(client):
    body = make_expense(client, source="voice").json()
    assert "source" not in body
    listed = client.get("/api/expenses").json()["items"][0]
    assert "source" not in listed


def test_2_2_amount_must_be_present_and_positive(client):
    for value, reason in [(None, "required"), (0, "must_be_positive"), (-5, "must_be_positive")]:
        error = make_expense(client, amount_cop=value).json()["error"]
        assert error["code"] == "validation"
        assert {"field": "amount_cop", "reason": reason} in error["fields"]


def test_2_3_category_and_method_are_named_when_missing(client):
    error = client.post("/api/expenses", json={"amount_cop": 1000}).json()["error"]
    reasons = {(f["field"], f["reason"]) for f in error["fields"]}
    assert ("category_id", "required") in reasons
    assert ("payment_method_id", "required") in reasons


def test_3_5_unknown_ids_are_rejected(client):
    error = make_expense(client, category_id=999).json()["error"]
    assert {"field": "category_id", "reason": "unknown_id"} in error["fields"]


def test_2_6_description_is_optional(client):
    assert make_expense(client, description=None).status_code == 201
    assert make_expense(client, description="").status_code == 201


def test_description_limit_is_1000(client):
    assert make_expense(client, description="x" * 1000).status_code == 201
    error = make_expense(client, description="x" * 1001).json()["error"]
    assert {"field": "description", "reason": "too_long"} in error["fields"]


def test_2_7_backdating_is_allowed_and_the_future_is_not(client):
    yesterday = (today() - timedelta(days=1)).isoformat()
    assert make_expense(client, spent_on=yesterday).status_code == 201
    tomorrow = (today() + timedelta(days=1)).isoformat()
    error = make_expense(client, spent_on=tomorrow).json()["error"]
    assert {"field": "spent_on", "reason": "future_date"} in error["fields"]


def test_5_1_every_field_is_editable_and_persists(client):
    expense_id = make_expense(client).json()["id"]
    patched = client.patch(
        f"/api/expenses/{expense_id}",
        json={
            "amount_cop": 22000,
            "category_id": 2,
            "payment_method_id": 2,
            "spent_on": (today() - timedelta(days=2)).isoformat(),
            "description": "corregido",
        },
    ).json()
    assert patched["amount_cop"] == 22000
    assert patched["category_name"] == "Transporte"
    assert patched["description"] == "corregido"
    assert client.get(f"/api/expenses/{expense_id}").json() == patched


def test_4_6_totals_reflect_edits_and_deletions(client):
    first = make_expense(client, amount_cop=10000).json()
    make_expense(client, amount_cop=5000)
    assert client.get("/api/summary/day").json()["total_cop"] == 15000

    client.patch(f"/api/expenses/{first['id']}", json={"amount_cop": 1000})
    assert client.get("/api/summary/day").json()["total_cop"] == 6000

    assert client.delete(f"/api/expenses/{first['id']}").status_code == 204
    assert client.get("/api/summary/day").json()["total_cop"] == 5000


def test_missing_expense_is_not_found(client):
    assert client.get("/api/expenses/4242").json()["error"]["code"] == "not_found"
    assert client.patch("/api/expenses/4242", json={"amount_cop": 1}).status_code == 404
    assert client.delete("/api/expenses/4242").status_code == 404


def test_4_1_list_is_newest_first(client):
    older = make_expense(client, spent_on=(today() - timedelta(days=3)).isoformat()).json()
    newer = make_expense(client).json()
    items = client.get("/api/expenses").json()["items"]
    assert [item["id"] for item in items] == [newer["id"], older["id"]]


def test_4_5_month_with_no_expenses_is_an_explicit_empty_state(client):
    body = client.get("/api/summary/month", params={"month": "2001-01"}).json()
    assert body["is_empty"] is True
    assert body["total_cop"] == 0
    assert body["by_category"] == []
    assert body["by_payment_method"] == []


def test_4_3_percentages_sum_to_100_and_are_ordered(client):
    make_expense(client, amount_cop=3333, category_id=1)
    make_expense(client, amount_cop=3333, category_id=2)
    make_expense(client, amount_cop=3334, category_id=3)
    body = client.get("/api/summary/month").json()
    percents = [item["percent"] for item in body["by_category"]]
    assert sum(percents) == 100
    amounts = [item["amount_cop"] for item in body["by_category"]]
    assert amounts == sorted(amounts, reverse=True)


def test_4_4_month_shows_totals_per_payment_method(client):
    make_expense(client, amount_cop=1000, payment_method_id=1)
    make_expense(client, amount_cop=2000, payment_method_id=2)
    body = client.get("/api/summary/month").json()
    totals = {item["name"]: item["amount_cop"] for item in body["by_payment_method"]}
    assert totals == {"Efectivo": 1000, "Tarjeta de crédito": 2000}


def test_4_7_a_previous_month_is_reachable_on_the_same_terms(client):
    body = client.get("/api/summary/month", params={"month": "2026-01"}).json()
    assert body["month"] == "2026-01"
    assert set(body) == {
        "month", "total_cop", "expense_count", "is_empty", "by_category", "by_payment_method"
    }


def test_malformed_month_is_a_validation_error(client):
    error = client.get("/api/summary/month", params={"month": "2026-13"}).json()["error"]
    assert error["code"] == "validation"


def test_expense_list_filters_by_month_and_day(client):
    make_expense(client, spent_on="2026-07-15")
    make_expense(client)
    by_month = client.get("/api/expenses", params={"month": "2026-07"}).json()
    assert by_month["total_count"] == 1
    by_day = client.get("/api/expenses", params={"date": "2026-07-15"}).json()
    assert by_day["total_count"] == 1
