"""Journal capture and browsing (Requirements 6, 7, 5.2, 5.3, 10.4)."""

from __future__ import annotations

from autonomos.clock import today


def test_6_1_entry_is_saved_against_today_and_listed_first(client):
    first = client.post("/api/journal", json={"text": "primera"}).json()
    second = client.post("/api/journal", json={"text": "segunda"}).json()
    assert first["written_at"][:10] == today().isoformat()
    items = client.get("/api/journal").json()["items"]
    assert [item["id"] for item in items] == [second["id"], first["id"]]


def test_6_2_blank_text_is_rejected(client):
    for text in ("", "   ", "\n\t "):
        error = client.post("/api/journal", json={"text": text}).json()["error"]
        assert {"field": "text", "reason": "blank"} in error["fields"]


def test_6_3_two_entries_on_one_day_stay_separate(client):
    a = client.post("/api/journal", json={"text": "uno"}).json()
    b = client.post("/api/journal", json={"text": "dos"}).json()
    assert a["id"] != b["id"]
    entries = client.get("/api/journal", params={"date": today().isoformat()}).json()
    assert len(entries["items"]) == 2
    assert {item["text"] for item in entries["items"]} == {"uno", "dos"}


def test_6_4_and_6_7_text_round_trips_byte_exact(client):
    text = "Línea uno\n\nLínea dos con ñ, ¿qué tal?  ¡Sí!\n\tSangría"
    created = client.post("/api/journal", json={"text": text}).json()
    assert created["text"] == text
    assert client.get(f"/api/journal/{created['id']}").json()["text"] == text


def test_6_5_a_long_entry_is_stored_and_returned_in_full(client):
    text = "a" * 5000 + " final"
    created = client.post("/api/journal", json={"text": text}).json()
    assert len(created["text"]) == len(text)
    assert client.get(f"/api/journal/{created['id']}").json()["text"] == text


def test_6_6_nothing_beyond_text_is_required(client):
    assert client.post("/api/journal", json={"text": "solo texto"}).status_code == 201


def test_10_4_source_is_not_returned(client):
    body = client.post("/api/journal", json={"text": "hablado", "source": "voice"}).json()
    assert "source" not in body
    assert "source" not in client.get("/api/journal").json()["items"][0]


def test_7_2_a_day_with_nothing_returns_an_empty_list(client):
    body = client.get("/api/journal", params={"date": "2001-05-05"}).json()
    assert body["items"] == []
    assert body["next_before"] is None


def test_7_3_no_entries_at_all_is_an_empty_list_not_an_error(client):
    response = client.get("/api/journal")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_5_3_editing_persists(client):
    created = client.post("/api/journal", json={"text": "borrador"}).json()
    patched = client.patch(f"/api/journal/{created['id']}", json={"text": "final"}).json()
    assert patched["text"] == "final"
    assert client.get(f"/api/journal/{created['id']}").json()["text"] == "final"


def test_patch_rejects_blank_text(client):
    created = client.post("/api/journal", json={"text": "algo"}).json()
    error = client.patch(f"/api/journal/{created['id']}", json={"text": " "}).json()["error"]
    assert error["code"] == "validation"


def test_5_2_delete_removes_only_after_the_call(client):
    created = client.post("/api/journal", json={"text": "temporal"}).json()
    assert client.delete(f"/api/journal/{created['id']}").status_code == 204
    assert client.get(f"/api/journal/{created['id']}").status_code == 404


def test_pagination_cursor(client):
    for i in range(5):
        client.post("/api/journal", json={"text": f"entrada {i}"})
    page = client.get("/api/journal", params={"limit": 2}).json()
    assert len(page["items"]) == 2
    assert page["next_before"] is not None
    second = client.get(
        "/api/journal", params={"limit": 2, "before": page["next_before"]}
    ).json()
    assert len(second["items"]) == 2
    assert {item["id"] for item in second["items"]} & {
        item["id"] for item in page["items"]
    } == set()
