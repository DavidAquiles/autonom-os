"""Categories and payment methods (Requirement 3)."""

from __future__ import annotations

import pytest

PATHS = ["/api/categories", "/api/payment-methods"]


@pytest.mark.parametrize("path", PATHS)
def test_3_1_starter_sets_are_non_empty_and_spanish(client, path):
    items = client.get(path).json()["items"]
    assert len(items) >= 6
    names = [item["name"] for item in items]
    assert "Comida" in names or "Efectivo" in names


@pytest.mark.parametrize("path", PATHS)
def test_3_2_creating_returns_the_new_row(client, path):
    response = client.post(path, json={"name": "Mascotas"})
    assert response.status_code == 201
    assert response.json()["name"] == "Mascotas"
    assert response.json()["archived"] is False


@pytest.mark.parametrize("path", PATHS)
def test_blank_and_overlong_names_are_rejected(client, path):
    blank = client.post(path, json={"name": "   "}).json()["error"]
    assert {"field": "name", "reason": "blank"} in blank["fields"]
    long = client.post(path, json={"name": "x" * 41}).json()["error"]
    assert {"field": "name", "reason": "too_long"} in long["fields"]


@pytest.mark.parametrize("path", PATHS)
def test_duplicate_active_name_conflicts(client, path):
    existing = client.get(path).json()["items"][0]["name"]
    response = client.post(path, json={"name": existing})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


@pytest.mark.parametrize("path", PATHS)
def test_recreating_an_archived_name_unarchives_it_with_200(client, path):
    created = client.post(path, json={"name": "Temporal"}).json()
    client.delete(f"{path}/{created['id']}")
    again = client.post(path, json={"name": "Temporal"})
    assert again.status_code == 200
    assert again.json()["id"] == created["id"]
    assert again.json()["archived"] is False


@pytest.mark.parametrize("path", PATHS)
def test_3_3_rename_shows_on_existing_expenses(client, path):
    item_id = client.get(path).json()["items"][0]["id"]
    field = "category_id" if "categories" in path else "payment_method_id"
    payload = {"amount_cop": 5000, "category_id": 1, "payment_method_id": 1}
    payload[field] = item_id
    expense_id = client.post("/api/expenses", json=payload).json()["id"]

    client.patch(f"{path}/{item_id}", json={"name": "Renombrado"})
    expense = client.get(f"/api/expenses/{expense_id}").json()
    name_field = "category_name" if "categories" in path else "payment_method_name"
    assert expense[name_field] == "Renombrado"


@pytest.mark.parametrize("path", PATHS)
def test_3_4_removal_warns_when_in_use_and_never_orphans(client, path):
    item_id = client.get(path).json()["items"][0]["id"]
    field = "category_id" if "categories" in path else "payment_method_id"
    payload = {"amount_cop": 5000, "category_id": 1, "payment_method_id": 1}
    payload[field] = item_id
    expense_id = client.post("/api/expenses", json=payload).json()["id"]

    blocked = client.delete(f"{path}/{item_id}")
    assert blocked.status_code == 409
    body = blocked.json()["error"]
    assert body["code"] == "in_use"
    assert body["details"]["affected_expenses"] == 1

    confirmed = client.delete(f"{path}/{item_id}", params={"confirm": "true"})
    assert confirmed.status_code == 200
    assert confirmed.json() == {"archived": True, "affected_expenses": 1}

    # The expense survives and still resolves the name it was filed under.
    assert client.get(f"/api/expenses/{expense_id}").status_code == 200
    # And the archived row is gone from selection.
    active = [item["id"] for item in client.get(path).json()["items"]]
    assert item_id not in active
    with_archived = [
        item["id"]
        for item in client.get(path, params={"include_archived": "true"}).json()["items"]
    ]
    assert item_id in with_archived


@pytest.mark.parametrize("path", PATHS)
def test_unknown_item_is_not_found(client, path):
    assert client.patch(f"{path}/999", json={"name": "x"}).status_code == 404
    assert client.delete(f"{path}/999").status_code == 404


def test_3_4_archived_category_still_appears_in_month_totals(client):
    created = client.post("/api/categories", json={"name": "Viaje"}).json()
    client.post(
        "/api/expenses",
        json={"amount_cop": 9000, "category_id": created["id"], "payment_method_id": 1},
    )
    client.delete(f"/api/categories/{created['id']}", params={"confirm": "true"})
    month = client.get("/api/summary/month").json()
    assert "Viaje" in [item["name"] for item in month["by_category"]]
