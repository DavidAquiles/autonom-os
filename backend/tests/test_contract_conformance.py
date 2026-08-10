"""Mechanical checks on the two things the design says Reviewer should check.

1. The HTTP surface is exactly the Interface Contract — no more, no less. R10
   makes this document the only thing keeping the two lanes in sync, and the
   frontend is built against it without seeing this code.
2. KD-7's boundary rule: no module outside `providers/` references Ollama,
   whisper.cpp, a model name, or a provider-specific field.
"""

from __future__ import annotations

from pathlib import Path

import pytest

CONTRACT_PATHS = {
    ("GET", "/api/health"),
    ("GET", "/api/status"),
    ("GET", "/api/categories"),
    ("POST", "/api/categories"),
    ("PATCH", "/api/categories/{item_id}"),
    ("DELETE", "/api/categories/{item_id}"),
    ("GET", "/api/payment-methods"),
    ("POST", "/api/payment-methods"),
    ("PATCH", "/api/payment-methods/{item_id}"),
    ("DELETE", "/api/payment-methods/{item_id}"),
    ("POST", "/api/expenses"),
    ("GET", "/api/expenses"),
    ("GET", "/api/expenses/{expense_id}"),
    ("PATCH", "/api/expenses/{expense_id}"),
    ("DELETE", "/api/expenses/{expense_id}"),
    ("POST", "/api/expenses/parse"),
    ("POST", "/api/expenses/suggest-category"),
    ("GET", "/api/summary/day"),
    ("GET", "/api/summary/month"),
    ("POST", "/api/journal"),
    ("GET", "/api/journal"),
    ("GET", "/api/journal/{entry_id}"),
    ("PATCH", "/api/journal/{entry_id}"),
    ("DELETE", "/api/journal/{entry_id}"),
    ("POST", "/api/voice/transcribe"),
    ("POST", "/api/insights/questions"),
    ("GET", "/api/insights/questions/{job_id}"),
    ("DELETE", "/api/insights/questions/{job_id}"),
    ("GET", "/api/insights/summaries/latest"),
    ("GET", "/api/export"),
}


def implemented_operations(client) -> set[tuple[str, str]]:
    schema = client.get("/api/openapi.json").json()
    return {
        (method.upper(), path)
        for path, methods in schema["paths"].items()
        for method in methods
    }


def test_every_contract_endpoint_exists(client):
    missing = CONTRACT_PATHS - implemented_operations(client)
    assert not missing, f"contract endpoints not implemented: {sorted(missing)}"


def test_no_endpoint_exists_beyond_the_contract(client):
    extra = implemented_operations(client) - CONTRACT_PATHS
    assert not extra, f"endpoints outside the contract: {sorted(extra)}"


# --- the query parameters of GET /api/expenses ----------------------------
#
# The two tests above compare `(method, path)` pairs, so a query parameter that
# appears, disappears or is renamed passes them untouched (R5). Every parameter
# this run added to the expense list is therefore unguarded by the repo's
# strictest gate, and the frontend is built against the written contract without
# seeing this code. Same closed-set treatment, asserted in both directions.

EXPENSE_LIST_QUERY_PARAMS = {
    "date",
    "month",
    "category_id",
    "order",
    "before_id",
    "limit",
    "offset",
}


def expense_list_query_parameters(client) -> set[str]:
    schema = client.get("/api/openapi.json").json()
    operation = schema["paths"]["/api/expenses"]["get"]
    return {
        parameter["name"]
        for parameter in operation.get("parameters", [])
        if parameter.get("in") == "query"
    }


def test_every_contracted_expense_list_parameter_exists(client):
    missing = EXPENSE_LIST_QUERY_PARAMS - expense_list_query_parameters(client)
    assert not missing, f"contract query parameters not implemented: {sorted(missing)}"


def test_no_expense_list_parameter_exists_beyond_the_contract(client):
    extra = expense_list_query_parameters(client) - EXPENSE_LIST_QUERY_PARAMS
    assert not extra, f"query parameters outside the contract: {sorted(extra)}"


# --- KD-7 boundary rule ---------------------------------------------------

VENDOR_TERMS = ("ollama", "whisper", "qwen", "llama", "ggml", "gguf")
PACKAGE = Path(__file__).resolve().parents[1] / "autonomos"
# `config.py` holds the env-var defaults KD-7 itself writes out
# (`LLM_MODEL=qwen2.5:3b-instruct-q4_K_M`), which is configuration rather than a
# code-level reference; a provider swap is still a config change with no code.
EXEMPT = {"config.py"}


def source_files() -> list[Path]:
    return [
        path
        for path in PACKAGE.rglob("*.py")
        if "providers" not in path.parts and path.name not in EXEMPT
    ]


@pytest.mark.parametrize("path", source_files(), ids=lambda p: p.name)
def test_no_vendor_name_outside_providers(path: Path):
    text = path.read_text(encoding="utf-8").lower()
    # Comments explaining *why* a decision was made may name a runtime; code
    # may not. Strip comment and docstring lines before looking.
    code = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )
    for chunk in code.split('"""')[::2]:  # drop docstring bodies
        for term in VENDOR_TERMS:
            assert term not in chunk, f"{path.name} references '{term}' outside providers/"
