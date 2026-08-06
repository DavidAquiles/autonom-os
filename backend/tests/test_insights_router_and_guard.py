"""QuestionRouter and NumericGuard — stages 1 and 4 of KD-10."""

from __future__ import annotations

from datetime import date

import pytest

from autonomos.insights import guard
from autonomos.insights.facts import FactSet
from autonomos.insights.router import PeriodUnrecognised, resolve_domain, route

REFERENCE = date(2026, 8, 5)  # a Wednesday


@pytest.mark.parametrize(
    "question,start,end",
    [
        ("¿cuánto gasté hoy?", "2026-08-05", "2026-08-05"),
        ("¿cuánto gasté ayer?", "2026-08-04", "2026-08-04"),
        ("¿qué gasté esta semana?", "2026-08-03", "2026-08-09"),
        ("¿qué gasté la semana pasada?", "2026-07-27", "2026-08-02"),
        ("¿cuánto llevo este mes?", "2026-08-01", "2026-08-31"),
        ("¿cuánto gasté el mes pasado?", "2026-07-01", "2026-07-31"),
        ("¿qué me preocupaba en julio?", "2026-07-01", "2026-07-31"),
        ("¿qué me preocupaba en julio de 2025?", "2025-07-01", "2025-07-31"),
        ("¿cuánto gasté este año?", "2026-01-01", "2026-12-31"),
        ("¿cuánto gasté en 2025?", "2025-01-01", "2025-12-31"),
    ],
)
def test_period_lexicon(question, start, end):
    resolved = route(None, question, REFERENCE)
    assert (resolved.period_start, resolved.period_end) == (start, end)
    assert resolved.period_assumed is False


def test_a_month_named_later_than_today_means_last_year():
    resolved = route(None, "¿qué gasté en diciembre?", REFERENCE)
    assert resolved.period_start == "2025-12-01"


@pytest.mark.parametrize(
    "question",
    [
        "¿cuánto gasté en los últimos tres meses?",
        "¿cuánto llevo desde que empecé?",
        "¿qué gasté en la primera quincena?",
        "¿cuánto gasté este trimestre?",
    ],
)
def test_11_11_an_unresolvable_period_is_a_failure_not_a_default(question):
    """A correct figure for the wrong period is the failure 11.11 guards
    against, and NumericGuard cannot catch it — the number *is* in the facts."""
    with pytest.raises(PeriodUnrecognised):
        route(None, question, REFERENCE)


def test_no_temporal_cue_defaults_to_the_current_month_and_says_so():
    resolved = route(None, "¿en qué se me va la plata?", REFERENCE)
    assert (resolved.period_start, resolved.period_end) == ("2026-08-01", "2026-08-31")
    assert resolved.period_assumed is True


def test_domain_detection(db):
    assert resolve_domain(db, "¿cuánto gasté en comida?") == "finances"
    assert resolve_domain(db, "¿qué escribí en el diario?") == "journal"
    assert resolve_domain(db, "¿qué pasó?") == "both"
    assert resolve_domain(db, "¿gasté más cuando escribí que estaba triste?") == "both"


def sample_facts() -> FactSet:
    facts = FactSet(
        period_label="julio de 2026",
        period_start="2026-07-01",
        period_end="2026-07-31",
        period_assumed=False,
        domain="finances",
        total_cop=250000,
        expense_count=12,
        distinct_days=9,
    )
    facts.by_category = [
        {"name": "Comida", "amount_cop": 150000, "percent": 60},
        {"name": "Transporte", "amount_cop": 100000, "percent": 40},
    ]
    return facts


def test_11_2_a_figure_from_the_facts_passes():
    facts = sample_facts()
    text = "En julio de 2026 gastaste 250.000 pesos, y 150.000 fueron en Comida (60%)."
    assert guard.check(text, facts).ok


def test_11_2_an_invented_figure_is_rejected():
    facts = sample_facts()
    result = guard.check("Gastaste 312.500 pesos en julio.", facts)
    assert result.ok is False
    assert result.offending  # reported in its normalised form


def test_a_percentage_outside_the_facts_is_rejected():
    assert guard.check("Comida fue el 63% del mes.", sample_facts()).ok is False


def test_a_computed_average_is_rejected():
    """The model must never compute: 250000/12 is not in the fact set."""
    assert guard.check("Tu promedio fue de 20.833 pesos.", sample_facts()).ok is False


def test_magnitude_words_are_resolved_before_checking():
    """`250 mil` is 250.000 — the same figure, so it must not be rejected, and
    `300 mil` is not in the facts, so it must be."""
    facts = sample_facts()
    assert guard.check("Gastaste 250 mil pesos.", facts).ok
    assert guard.check("Gastaste 300 mil pesos.", facts).ok is False


def test_spaced_thousands_are_read_as_one_figure():
    assert guard.check("Gastaste 250 000 pesos.", sample_facts()).ok


def test_text_without_figures_always_passes():
    assert guard.check("No puedo responder eso con lo que hay registrado.", sample_facts()).ok


def test_dates_inside_the_period_are_verifiable():
    facts = sample_facts()
    assert guard.check("Entre el 1 y el 31 de julio de 2026 gastaste 250.000.", facts).ok


def facts_with_prompt_details() -> FactSet:
    """Facts carrying exactly what `render_facts` exposes beyond the aggregates:
    a top expense with a date and a description, and a dated journal excerpt."""
    from autonomos.insights.facts import JournalExcerpt

    facts = sample_facts()
    facts.domain = "both"
    facts.top_expenses = [
        {
            "amount_cop": 45000,
            "spent_on": "2026-07-14",
            "category_name": "Comida",
            "description": "cena para 4 personas",
        }
    ]
    facts.journal_entries_considered = 2
    facts.journal_entries_used = 2
    facts.journal_excerpts = [
        JournalExcerpt("2026-07-22T21:00:00.000-05:00", "Me gasté como 30 mil en el bar."),
    ]
    return facts


def test_f3_a_top_expense_date_the_prompt_showed_is_verifiable():
    """The prompt writes `- Gasto grande: 45.000 pesos el 2026-07-14 …` and tells
    the model it may repeat any figure in DATOS. The guard must therefore accept
    `el 14 de julio`, or a correct answer is terminated `unverifiable_figures`."""
    facts = facts_with_prompt_details()
    result = guard.check(
        "El gasto más grande fue de 45.000 pesos el 14 de julio, en Comida.", facts
    )
    assert result.ok, f"rejected figures the prompt authorised: {result.offending}"


def test_f3_a_journal_excerpt_date_and_its_digits_are_verifiable():
    facts = facts_with_prompt_details()
    assert guard.check("El 22 de julio escribiste sobre el bar.", facts).ok
    # A figure the user wrote in their own entry is data they can verify.
    assert guard.check("Escribiste que gastaste como 30 mil en el bar.", facts).ok
    # As is a number inside a description the prompt showed.
    assert guard.check("Fue una cena para 4 personas.", facts).ok


def test_f3_the_guard_still_catches_a_date_that_is_not_in_the_facts():
    """The fix widens the set to what the prompt exposes — not to any date."""
    facts = facts_with_prompt_details()
    assert guard.check("El gasto más grande fue el 19 de julio.", facts).ok is False


def test_f3_widening_did_not_weaken_the_core_property():
    """With top expenses and excerpts present, an invented total, a computed
    average, an out-of-set percentage and an invented count are all still
    caught (11.2)."""
    facts = facts_with_prompt_details()
    assert guard.check("Gastaste 312.500 pesos en julio.", facts).ok is False
    assert guard.check("Tu promedio diario fue de 20.833 pesos.", facts).ok is False
    assert guard.check("Comida fue el 63% del mes.", facts).ok is False
    assert guard.check("Tienes 88 entradas de diario.", facts).ok is False


def test_the_guard_is_membership_not_meaning_and_this_predates_f3():
    """A documented limit, asserted so nobody mistakes it for a regression.

    The guard checks that a figure *appears* in the fact set, not that it is
    used correctly, so a small integer present for one reason authorises it
    everywhere — `7` is allowed by the period month `2026-07` alone. This is
    true of the pre-F3 guard too (the period bounds always contributed their
    year/month/day), and KD-10 says as much when it explains that a correct
    figure for the wrong period is something NumericGuard cannot see. What
    covers that is the router's `period_unrecognised`, not this.
    """
    bare = sample_facts()  # no top expenses, no excerpts: the pre-F3 shape
    assert 7.0 in guard.allowed_values(bare)
    assert guard.check("Hay 7 entradas.", bare).ok


def test_f3_the_allowed_set_is_derived_from_what_the_model_was_shown():
    """The guard's set and the prompt's DATOS block cannot drift, because the
    set is scanned out of that block."""
    from autonomos.insights.prompts import render_facts

    facts = facts_with_prompt_details()
    allowed = guard.allowed_values(facts)
    rendered = render_facts(facts)
    assert "2026-07-14" in rendered and "cena para 4 personas" in rendered
    for value in (45000.0, 14.0, 22.0, 4.0, 30000.0):
        assert value in allowed, f"{value} is in DATOS but not in the allowed set"
