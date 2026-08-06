"""The Spanish numeral grammar and the rules extractor (2.4, 9.1, 9.2, 9.6, 9.7)."""

from __future__ import annotations

import pytest

from autonomos.db import get_db
from autonomos.parsing.extractor import parse_expense_text, resolve_amount
from autonomos.parsing.numerals import parse_spanish_number
from autonomos.parsing.text import trim_on_word_boundary


@pytest.mark.parametrize(
    "text,expected",
    [
        ("14.000", 14000),
        ("14000", 14000),
        ("14 000", 14000),
        ("14,000", 14000),
        ("catorce mil", 14000),
        ("14 mil", 14000),
        ("mil quinientos", 1500),
        ("dos mil quinientos", 2500),
        ("un millon doscientos mil", 1200000),
        ("un millón doscientos mil", 1200000),
        ("ciento cincuenta mil", 150000),
        ("treinta y cinco mil", 35000),
        ("cien", 100),
        ("novecientos noventa y nueve mil", 999000),
        ("1.250.000", 1250000),
    ],
)
def test_spanish_number_forms(text, expected):
    assert parse_spanish_number(text) == expected


@pytest.mark.parametrize("text", ["", "hola", "mil mil", "cinco cinco"])
def test_non_numbers_return_none(text):
    assert parse_spanish_number(text) is None


def test_2_4_three_written_forms_are_the_same_value():
    """2.4: `14.000`, `14000` and `14 000` are all fourteen thousand pesos."""
    values = {resolve_amount(f"gasté {form} pesos en el almuerzo")
              for form in ("14.000", "14000", "14 000")}
    assert values == {14000}


def test_9_6_spoken_forms_resolve_to_the_same_value():
    for phrase in ("catorce mil", "14 mil", "14.000"):
        assert resolve_amount(f"gasté {phrase} pesos en uber") == 14000


def test_9_2_two_equally_cued_amounts_yield_nothing():
    """Two candidates with equal cue strength: amount is null, not a guess."""
    assert resolve_amount("gasté 14.000 pesos y 20.000 pesos") is None


def test_time_of_day_is_not_an_amount():
    assert resolve_amount("a las 3 compré un café de 5.000 pesos") == 5000


def test_9_1_full_sentence_prefills_every_field(db):
    draft = parse_expense_text(
        db, "gasté 14.000 pesos en Uber con la tarjeta de crédito"
    )
    assert draft.amount_cop == 14000
    assert draft.category_name == "Transporte"
    assert draft.payment_method_name == "Tarjeta de crédito"
    assert draft.resolved_by == {
        "amount": "rules",
        "category": "rules",
        "payment_method": "rules",
    }
    assert draft.description == "gasté 14.000 pesos en Uber con la tarjeta de crédito"


def test_9_7_everyday_payment_phrases(db):
    assert parse_expense_text(db, "pagué en efectivo").payment_method_name == "Efectivo"
    assert parse_expense_text(db, "lo pagué en plata").payment_method_name == "Efectivo"
    assert (
        parse_expense_text(db, "con la tarjeta débito").payment_method_name
        == "Tarjeta débito"
    )
    assert parse_expense_text(db, "por nequi").payment_method_name == "Nequi"


def test_9_2_unknown_method_and_category_stay_empty(db):
    draft = parse_expense_text(db, "gasté 9.000 en algo raro")
    assert draft.payment_method_id is None
    assert draft.category_id is None
    assert draft.resolved_by["payment_method"] == "none"
    assert draft.resolved_by["category"] == "none"


def test_9_3_category_is_always_an_existing_row(db):
    draft = parse_expense_text(db, "almuerzo de 20.000")
    ids = {row["id"] for row in db.execute("SELECT id FROM categories").fetchall()}
    assert draft.category_id in ids


def test_description_is_trimmed_on_a_word_boundary():
    text = "palabra " * 200  # 1600 characters
    trimmed, truncated = trim_on_word_boundary(text.strip(), 1000)
    assert truncated is True
    assert len(trimmed) <= 1000
    assert not trimmed.endswith("palab")


def test_long_transcript_marks_description_truncated(db):
    long_text = "gasté 14.000 pesos " + ("comprando cosas " * 100)
    draft = parse_expense_text(db, long_text)
    assert draft.description_truncated is True
    assert len(draft.description) <= 1000
    assert draft.amount_cop == 14000
