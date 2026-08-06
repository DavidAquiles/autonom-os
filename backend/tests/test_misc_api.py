"""Health, status, category assist, export and the error envelope itself."""

from __future__ import annotations

import json

from autonomos.errors import ERROR_CODES
from autonomos.insights.facts import build_facts
from autonomos.insights.router import Route


def test_health_reports_the_server_clock_and_timezone(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["tz"] == "America/Bogota"
    assert body["server_time"].endswith("-05:00")
    assert body["version"]


def _certs(tmp_path):
    cert, key = tmp_path / "c.pem", tmp_path / "k.pem"
    cert.write_text("cert")
    key.write_text("key")
    return str(cert), str(key)


def test_13_8_health_advertises_both_origins(client, monkeypatch, tmp_path):
    """KD-2 mechanism 1: the client learns the *other* origin while the server
    is reachable, because at the moment it needs it nothing will answer."""
    from autonomos.config import reset_settings

    cert, key = _certs(tmp_path)
    monkeypatch.setenv("PUBLIC_URL", "https://autonomos.tail1a2b3c.ts.net")
    monkeypatch.setenv("LAN_BIND_ADDR", "192.168.1.42")
    monkeypatch.setenv("LAN_PORT", "8443")
    monkeypatch.setenv("TLS_CERTFILE", cert)
    monkeypatch.setenv("TLS_KEYFILE", key)
    reset_settings()

    origins = client.get("/api/health").json()["origins"]
    assert origins == {
        "primary": "https://autonomos.tail1a2b3c.ts.net",
        "lan": "https://192.168.1.42:8443",
    }


def test_origins_are_absolute_with_no_trailing_path(client, monkeypatch):
    from autonomos.config import reset_settings

    monkeypatch.setenv("PUBLIC_URL", "https://autonomos.tail1a2b3c.ts.net/finanzas/")
    reset_settings()
    assert (
        client.get("/api/health").json()["origins"]["primary"]
        == "https://autonomos.tail1a2b3c.ts.net"
    )


def test_unconfigured_origins_are_null_not_missing_and_not_an_error(client):
    body = client.get("/api/health")
    assert body.status_code == 200
    assert body.json()["origins"] == {"primary": None, "lan": None}


def test_lan_origin_is_null_whenever_the_fallback_listener_is_disabled(
    client, monkeypatch, tmp_path
):
    """Advertising an origin nothing is listening on is a lie the client would
    act on during an outage, so the advertisement uses the listener's own
    predicate."""
    from autonomos.config import reset_settings

    cert, key = _certs(tmp_path)
    monkeypatch.setenv("PUBLIC_URL", "https://autonomos.tail1a2b3c.ts.net")

    # 1. no bind address configured
    monkeypatch.setenv("LAN_BIND_ADDR", "")
    reset_settings()
    assert client.get("/api/health").json()["origins"]["lan"] is None

    # 2. 0.0.0.0 is refused by KD-2, so nothing listens
    monkeypatch.setenv("LAN_BIND_ADDR", "0.0.0.0")
    monkeypatch.setenv("TLS_CERTFILE", cert)
    monkeypatch.setenv("TLS_KEYFILE", key)
    reset_settings()
    assert client.get("/api/health").json()["origins"]["lan"] is None

    # 3. certificate missing, so the TLS listener cannot start
    monkeypatch.setenv("LAN_BIND_ADDR", "192.168.1.42")
    monkeypatch.setenv("TLS_CERTFILE", str(tmp_path / "absent.pem"))
    reset_settings()
    assert client.get("/api/health").json()["origins"]["lan"] is None

    # …and the primary is unaffected throughout.
    assert (
        client.get("/api/health").json()["origins"]["primary"]
        == "https://autonomos.tail1a2b3c.ts.net"
    )


def test_origins_are_never_derived_from_the_request(client, monkeypatch):
    """A Host header would echo the origin the client is already on — precisely
    the one that is useless during an outage."""
    from autonomos.config import reset_settings

    monkeypatch.setenv("PUBLIC_URL", "https://autonomos.tail1a2b3c.ts.net")
    reset_settings()
    body = client.get(
        "/api/health",
        headers={"Host": "192.168.1.99:8443", "X-Forwarded-Host": "evil.example.com"},
    ).json()
    assert body["origins"]["primary"] == "https://autonomos.tail1a2b3c.ts.net"
    assert body["origins"]["lan"] is None


def test_the_listener_and_the_advertisement_share_one_predicate(monkeypatch, tmp_path):
    """`serve.py` and `/api/health` must never disagree about whether the LAN
    fallback exists."""
    from autonomos.config import (
        get_settings,
        lan_fallback_status,
        lan_origin,
        reset_settings,
    )

    cert, key = _certs(tmp_path)
    monkeypatch.setenv("LAN_BIND_ADDR", "192.168.1.42")
    monkeypatch.setenv("TLS_CERTFILE", cert)
    monkeypatch.setenv("TLS_KEYFILE", key)
    reset_settings()
    assert lan_fallback_status(get_settings())[0] is True
    assert lan_origin() == "https://192.168.1.42:8443"

    monkeypatch.setenv("LAN_BIND_ADDR", "0.0.0.0")
    reset_settings()
    enabled, reason = lan_fallback_status(get_settings())
    assert enabled is False and "0.0.0.0" in reason
    assert lan_origin() is None


def test_status_reports_both_sidecars(client):
    body = client.get("/api/status").json()
    assert body["transcription"] == "ok"
    assert body["llm"] == "ok"
    assert body["checked_at"]


def test_error_envelope_shape_and_closed_code_set(client):
    body = client.get("/api/expenses/999").json()
    assert set(body) == {"error"}
    assert set(body["error"]) >= {"code", "message", "details"}
    assert body["error"]["code"] in ERROR_CODES
    validation = client.post("/api/expenses", json={}).json()["error"]
    assert validation["code"] == "validation"
    assert isinstance(validation["fields"], list)
    for field in validation["fields"]:
        assert set(field) == {"field", "reason"}


def test_a_non_integer_amount_is_a_validation_error_not_a_framework_error(client):
    response = client.post(
        "/api/expenses",
        json={"amount_cop": "mucho", "category_id": 1, "payment_method_id": 1},
    )
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "validation"
    assert {"field": "amount_cop", "reason": "not_an_integer"} in error["fields"]


def test_unknown_api_path_returns_the_envelope(client):
    response = client.get("/api/gym")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_kd16_there_is_no_gym_endpoint(client):
    """Gym is a frontend route and nothing else; any backend Gym work is scope
    creep to be rejected at review (KD-16)."""
    paths = client.get("/api/openapi.json").json()["paths"]
    assert not [path for path in paths if "gym" in path or "gimnasio" in path]


def test_no_csv_export_endpoints_exist(client):
    """CSV exports were cut at the Approve Plan gate and must not be built."""
    paths = client.get("/api/openapi.json").json()["paths"]
    assert not [path for path in paths if path.endswith(".csv")]
    assert client.get("/api/export/expenses.csv").status_code == 404


def test_14_2_export_is_a_lossless_json_dump(client):
    client.post(
        "/api/expenses",
        json={
            "amount_cop": 14000,
            "category_id": 1,
            "payment_method_id": 1,
            "description": "almuerzo",
            "source": "voice",
        },
    )
    client.post("/api/journal", json={"text": "Una entrada con ñ y tildes."})
    response = client.get("/api/export")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    body = json.loads(response.text)
    assert body["schema_version"] >= 1
    assert set(body) >= {
        "exported_at", "categories", "payment_methods", "expenses", "journal_entries",
        "summaries",
    }
    expense = body["expenses"][0]
    # ids *and* names, so the file reads without this app
    assert expense["category_id"] == 1 and expense["category_name"] == "Comida"
    assert expense["source"] == "voice"  # the archival dump is the one place
    assert body["journal_entries"][0]["text"] == "Una entrada con ñ y tildes."


def test_9_3_assist_falls_back_to_rules_without_calling_the_model(client, fake_llm):
    body = client.post(
        "/api/expenses/suggest-category", json={"text": "almuerzo en el restaurante"}
    ).json()
    assert body["source"] == "rules"
    assert body["category_name"] == "Comida"
    assert fake_llm.calls == []


def test_assist_uses_the_model_when_the_rules_find_nothing(client, fake_llm):
    fake_llm.response = "Ocio"
    body = client.post(
        "/api/expenses/suggest-category", json={"text": "entradas para el partido"}
    ).json()
    assert body["source"] == "llm"
    assert body["category_name"] == "Ocio"
    assert body["category_id"] is not None


def test_9_3_a_model_answer_outside_the_list_is_discarded(client, fake_llm):
    fake_llm.response = "Criptomonedas"
    body = client.post(
        "/api/expenses/suggest-category", json={"text": "algo muy raro"}
    ).json()
    assert body == {"category_id": None, "category_name": None, "source": "none"}


def test_assist_never_fails_the_caller(client, fake_llm):
    from autonomos.providers.base import ProviderUnavailable

    fake_llm.raise_error = ProviderUnavailable("down")
    response = client.post("/api/expenses/suggest-category", json={"text": "cosa rara"})
    assert response.status_code == 200
    assert response.json()["source"] == "none"


def test_assist_on_empty_text_is_none(client):
    body = client.post("/api/expenses/suggest-category", json={"text": "  "}).json()
    assert body["source"] == "none"


def test_journal_context_budget_truncates_and_says_so(db, monkeypatch):
    from autonomos.clock import now_iso

    for index in range(40):
        text = "palabra " * 200  # ~1600 characters, ~460 tokens each
        db.execute(
            "INSERT INTO journal_entries(text, written_at, source, created_at, updated_at) "
            "VALUES(?,?,'manual',?,?)",
            (text, f"2026-07-{index % 28 + 1:02d}T10:00:00.000-05:00", now_iso(), now_iso()),
        )
    route = Route("2026-07-01", "2026-07-31", "julio de 2026", False, "journal")
    facts = build_facts(db, route, kind="question")
    assert facts.journal_entries_considered == 40
    assert facts.journal_entries_used < 40
    assert facts.journal_truncated is True


def test_summary_journal_selection_spreads_across_the_month(db):
    from autonomos.clock import now_iso

    for day in range(1, 29):
        db.execute(
            "INSERT INTO journal_entries(text, written_at, source, created_at, updated_at) "
            "VALUES(?,?,'manual',?,?)",
            (f"dia {day} " + "x" * 200, f"2026-07-{day:02d}T10:00:00.000-05:00",
             now_iso(), now_iso()),
        )
    route = Route("2026-07-01", "2026-07-31", "julio de 2026", False, "both")
    facts = build_facts(db, route, kind="summary")
    days = [excerpt.written_at[8:10] for excerpt in facts.journal_excerpts]
    assert days == sorted(days)  # oldest first, one per day
    assert len(set(days)) == len(days)
    assert "01" in days
