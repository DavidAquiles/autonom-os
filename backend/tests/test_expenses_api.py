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


def test_d5_an_amount_past_the_storage_limit_is_a_clean_validation_error(client):
    """QA D5: `999999999999999999999` reached the driver and came back as a 500
    carrying `OverflowError: Python int too large to convert to SQLite INTEGER`.
    Every other bad amount gets a clean rejection naming the field; so does this
    one now."""
    response = make_expense(client, amount_cop=999999999999999999999)
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "validation"
    assert {"field": "amount_cop", "reason": "too_long"} in error["fields"]
    assert client.get("/api/expenses").json()["total_count"] == 0


def test_d5_the_largest_storable_amount_is_still_accepted(client):
    assert make_expense(client, amount_cop=2**63 - 1).status_code == 201
    assert make_expense(client, amount_cop=2**63).status_code == 400


def test_d5_an_absurd_amount_on_patch_is_also_rejected(client):
    expense_id = make_expense(client).json()["id"]
    response = client.patch(
        f"/api/expenses/{expense_id}", json={"amount_cop": 10**30}
    )
    assert response.status_code == 400
    assert client.get(f"/api/expenses/{expense_id}").json()["amount_cop"] == 14000


def test_d7_an_archived_category_is_refused_for_a_new_expense(client):
    """QA D7: 3.4 says a removed category is gone from future selection. The UI
    hides the chip; the API now enforces it too."""
    created = client.post("/api/categories", json={"name": "Temporal"}).json()
    client.delete(f"/api/categories/{created['id']}")

    response = make_expense(client, category_id=created["id"])
    assert response.status_code == 400
    assert {"field": "category_id", "reason": "unknown_id"} in response.json()["error"]["fields"]


def test_d7_an_archived_payment_method_is_refused_for_a_new_expense(client):
    created = client.post("/api/payment-methods", json={"name": "Temporal"}).json()
    client.delete(f"/api/payment-methods/{created['id']}")
    response = make_expense(client, payment_method_id=created["id"])
    assert response.status_code == 400
    assert (
        {"field": "payment_method_id", "reason": "unknown_id"}
        in response.json()["error"]["fields"]
    )


def test_d7_an_old_expense_under_an_archived_category_stays_editable(client):
    """3.4 keeps historical expenses attributed to the archived name, so editing
    one must not become impossible — only *moving* an expense onto an archived
    category is refused."""
    created = client.post("/api/categories", json={"name": "Temporal"}).json()
    expense_id = make_expense(client, category_id=created["id"]).json()["id"]
    client.delete(f"/api/categories/{created['id']}", params={"confirm": "true"})

    # Editing another field, with the archived category left in place.
    assert client.patch(f"/api/expenses/{expense_id}", json={"amount_cop": 9000}).status_code == 200
    # Re-sending the same (archived) category is still accepted…
    assert (
        client.patch(
            f"/api/expenses/{expense_id}", json={"category_id": created["id"]}
        ).status_code
        == 200
    )
    # …and moving it to an active one works.
    assert client.patch(f"/api/expenses/{expense_id}", json={"category_id": 1}).status_code == 200
    # But moving a different expense *onto* the archived one is refused.
    other = make_expense(client).json()["id"]
    assert (
        client.patch(
            f"/api/expenses/{other}", json={"category_id": created["id"]}
        ).status_code
        == 400
    )


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


# --- Historial: registration order, keyset paging (Requirement 16) ---------
#
# Dates are taken relative to `today()` so the suite does not rot: `a_day_in`
# walks backwards from the last day of the previous month, which is always in
# that month for any offset under 28.


def last_month_day(offset: int = 0) -> str:
    """A date inside the previous calendar month, `offset` days before its end."""
    end_of_last_month = today().replace(day=1) - timedelta(days=1)
    return (end_of_last_month - timedelta(days=offset)).isoformat()


def last_month() -> str:
    return last_month_day()[:7]


def listed(client, **params) -> dict:
    response = client.get("/api/expenses", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def ids(body: dict) -> list[int]:
    return [item["id"] for item in body["items"]]


def test_16_2_historial_is_ordered_by_when_it_was_recorded_not_by_its_date(client):
    """`order=registered` ignores `spent_on` entirely. The three below are
    recorded newest-date-first, so the two orderings are exact opposites and
    neither result can be produced by the other's SQL."""
    first = make_expense(client, spent_on=last_month_day(0)).json()
    second = make_expense(client, spent_on=last_month_day(10)).json()
    third = make_expense(client, spent_on=last_month_day(20)).json()

    assert ids(listed(client, order="registered")) == [
        third["id"], second["id"], first["id"]
    ]
    assert ids(listed(client)) == [first["id"], second["id"], third["id"]]


def test_16_3_an_expense_dated_in_the_past_is_at_the_top_of_historial(client):
    """Recorded last, dated earliest — 16.3 puts it first anyway."""
    dated_today = make_expense(client).json()
    backdated = make_expense(client, spent_on=last_month_day(3)).json()

    assert ids(listed(client, order="registered"))[0] == backdated["id"]
    # The default (date) ordering is where it sinks below the newer date.
    assert ids(listed(client))[0] == dated_today["id"]


def test_16_4_editing_an_expense_does_not_move_it_in_historial(client):
    first = make_expense(client).json()["id"]
    middle = make_expense(client).json()["id"]
    last = make_expense(client).json()["id"]
    before = ids(listed(client, order="registered"))

    client.patch(
        f"/api/expenses/{middle}",
        json={"amount_cop": 99000, "spent_on": last_month_day(5)},
    )

    assert ids(listed(client, order="registered")) == before == [last, middle, first]


def test_16_7_paging_appends_older_records_without_repeating_or_reordering(client):
    recorded = [make_expense(client).json()["id"] for _ in range(7)]
    expected = list(reversed(recorded))

    first_page = listed(client, order="registered", limit=3)
    assert ids(first_page) == expected[:3]
    assert first_page["next_before_id"] == expected[2]

    second_page = listed(
        client, order="registered", limit=3, before_id=first_page["next_before_id"]
    )
    assert ids(second_page) == expected[3:6]
    assert not set(ids(first_page)) & set(ids(second_page))


def test_16_8_repeated_paging_reaches_the_very_first_expense_ever_recorded(client):
    recorded = [make_expense(client).json()["id"] for _ in range(7)]

    seen: list[int] = []
    cursor = None
    for _ in range(10):  # bounded, so a non-terminating cursor fails rather than hangs
        page = listed(
            client,
            order="registered",
            limit=2,
            **({"before_id": cursor} if cursor is not None else {}),
        )
        seen.extend(ids(page))
        cursor = page["next_before_id"]
        if cursor is None:
            break

    assert cursor is None
    assert seen == list(reversed(recorded))
    assert seen[-1] == recorded[0]


def test_16_9_the_last_page_presents_no_cursor(client):
    for _ in range(4):
        make_expense(client)
    assert listed(client, order="registered", limit=4)["next_before_id"] is None
    assert listed(client, order="registered", limit=10)["next_before_id"] is None
    # Nothing recorded at all is also "everything is shown".
    empty = listed(client, order="registered", month="2001-01")
    assert empty["items"] == [] and empty["next_before_id"] is None


def test_16_13_the_first_screenful_does_not_fetch_every_expense(client):
    for _ in range(9):
        make_expense(client)
    page = listed(client, order="registered", limit=3)
    assert len(page["items"]) == 3
    assert page["total_count"] == 9


def test_before_id_never_returns_the_cursor_row(client):
    recorded = [make_expense(client).json()["id"] for _ in range(4)]
    page = listed(client, order="registered", before_id=recorded[2])
    assert ids(page) == [recorded[1], recorded[0]]


def test_before_id_with_the_default_order_is_accepted_and_reports_no_cursor(client):
    """The combination is defined and serves no criterion: it filters, and its
    cursor is always `null` (Interface Contract, `before_id`)."""
    recorded = [make_expense(client).json()["id"] for _ in range(4)]
    page = listed(client, before_id=recorded[2], limit=1)
    assert page["next_before_id"] is None
    assert ids(page) == [recorded[1]]


def test_the_default_order_is_unchanged_and_carries_a_null_cursor(client):
    """Nothing that exists changed: no new parameter means today's ordering,
    today's two fields, and a null cursor."""
    older = make_expense(client, spent_on=last_month_day(2)).json()
    newer = make_expense(client).json()
    body = listed(client)
    assert set(body) == {"items", "total_count", "next_before_id"}
    assert ids(body) == [newer["id"], older["id"]]
    assert body["total_count"] == 2
    assert body["next_before_id"] is None


def test_day_and_month_summaries_still_read_through_the_widened_list(client):
    make_expense(client, amount_cop=1000)
    make_expense(client, amount_cop=2000)
    day = client.get("/api/summary/day").json()
    assert day["total_cop"] == 3000 and day["expense_count"] == 2
    assert client.get("/api/summary/month").json()["expense_count"] == 2


# --- The month's category drill-down (Requirement 18) ----------------------


def test_18_2_a_selected_category_shows_only_it_and_only_the_viewed_month(client):
    wanted = make_expense(client, category_id=1, spent_on=last_month_day(4)).json()
    make_expense(client, category_id=2, spent_on=last_month_day(4))  # other category
    make_expense(client, category_id=1)  # same category, this month

    body = listed(client, month=last_month(), category_id=1)
    assert ids(body) == [wanted["id"]]
    assert body["total_count"] == 1


def test_18_2_an_unknown_category_is_an_empty_list_not_an_error(client):
    make_expense(client)
    body = listed(client, category_id=9999)
    assert body["items"] == []
    assert body["total_count"] == 0
    assert body["next_before_id"] is None


def test_18_2_an_archived_categorys_expenses_stay_reachable(client):
    """3.4 keeps historical expenses attributed to an archived category and it
    still appears in `by_category`, so the filter must not exclude it."""
    created = client.post("/api/categories", json={"name": "Temporal"}).json()
    expense = make_expense(client, category_id=created["id"]).json()
    client.delete(f"/api/categories/{created['id']}", params={"confirm": "true"})

    body = listed(client, category_id=created["id"])
    assert ids(body) == [expense["id"]]
    assert body["items"][0]["category_name"] == "Temporal"


def test_18_13_a_filtered_category_list_is_ordered_by_the_date_it_is_dated_for(client):
    """Deliberately *not* Historial's order: recorded newest-date-last, shown
    newest-date-first."""
    oldest = make_expense(client, category_id=1, spent_on=last_month_day(9)).json()
    middle = make_expense(client, category_id=1, spent_on=last_month_day(5)).json()
    newest = make_expense(client, category_id=1, spent_on=last_month_day(1)).json()

    body = listed(client, month=last_month(), category_id=1)
    assert ids(body) == [newest["id"], middle["id"], oldest["id"]]
    assert body["next_before_id"] is None


def test_18_3_total_count_ignores_before_id_limit_and_offset(client):
    recorded = [make_expense(client, category_id=1).json()["id"] for _ in range(5)]
    make_expense(client, category_id=2)

    assert listed(client, category_id=1)["total_count"] == 5
    assert listed(client, category_id=1, limit=2)["total_count"] == 5
    assert listed(client, category_id=1, offset=3)["total_count"] == 5
    assert listed(client, category_id=1, before_id=recorded[1])["total_count"] == 5


def test_the_new_list_parameters_are_rejected_within_the_closed_reason_set(client):
    cases = [
        ({"category_id": 0}, ("category_id", "must_be_positive")),
        ({"category_id": "abc"}, ("category_id", "not_an_integer")),
        ({"before_id": 0}, ("before_id", "must_be_positive")),
        ({"before_id": "x"}, ("before_id", "not_an_integer")),
        ({"order": "fecha"}, ("order", "required")),
    ]
    for params, (field, reason) in cases:
        response = client.get("/api/expenses", params=params)
        assert response.status_code == 400, params
        error = response.json()["error"]
        assert error["code"] == "validation"
        assert {"field": field, "reason": reason} in error["fields"], params
