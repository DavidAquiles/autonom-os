"""NumericGuard — stage 4 of KD-10.

Every numeric token in generated text must appear in the fact set after
normalisation. A figure that does not is a hallucination, and 11.2 makes that a
defect rather than a quirk. On violation the runner retries once with a stricter
prompt and then fails explicitly with `unverifiable_figures`.

**The fact set is typed, and membership is checked within type.** Two real
defects, pulling in opposite directions, are what forced this:

* Reviewer F3 — a hand-listed allowed set omitted the dates the prompt itself
  writes into DATOS, so a correct "el 14 de julio" was rejected and the job
  died `unverifiable_figures`. The set must therefore cover everything the
  model was shown.
* QA D8 — once it did, a *date component* could launder itself into a
  *quantity*: a summary said "durante los días con algún gasto **(20)**" where
  July had 3, and `20` passed only because 20 July was a top-expense date.

So a date may be stated **as a date** and is validated as a whole date against
the dates in the fact set, while quantities — money, counts, percentages — are
checked against quantities alone. Neither defect can return: widening for F3
does not feed D8, and closing D8 does not narrow the set back.

What this does **not** cover is stated plainly in KD-10: 11.1 (no outside facts
or advice) and 11.7 (Spanish) are prompt-enforced, not guarded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .facts import FactSet

# A digit-bearing figure, optionally scaled by a Spanish magnitude word.
_FIGURE_RE = re.compile(r"(\d+(?:[.,]\d+)*)\s*(millones|millon|mil)?", re.IGNORECASE)
_MAGNITUDE = {"mil": 1_000, "millon": 1_000_000, "millones": 1_000_000}
_GROUPED = re.compile(r"^\d{1,3}(?:[.,  ]\d{3})+$")

_MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}
_MONTH_ALTERNATION = "|".join(_MONTHS_ES)

# `2026-07-14` — how every date reaches the model in DATOS.
_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
# `el 14 de julio`, `del 1 al 15 de julio de 2026`, `el 1 y el 31 de julio` —
# how a date comes back out in Spanish prose. At most two days per phrase,
# which covers a single date and a range.
_ES_DATE_RE = re.compile(
    r"\b(\d{1,2})"
    r"(?:\s*(?:,|y|al|a|hasta|-|—)\s*(?:el\s+)?(\d{1,2}))?"
    rf"\s+de\s+({_MONTH_ALTERNATION})"
    r"(?:\s+del?\s+(\d{4}))?\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    offending: list[str]


def _numeric_value(raw: str, magnitude: str | None) -> float | None:
    token = raw.strip().replace(" ", " ")
    if _GROUPED.match(token):
        value: float = float(token.replace(".", "").replace(",", "").replace(" ", ""))
    elif token.isdigit():
        value = float(token)
    else:
        cleaned = token.replace(" ", "").replace(".", "@").replace(",", "@")
        parts = cleaned.split("@")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            value = float(f"{parts[0]}.{parts[1]}")  # a decimal such as 1,5
        elif all(part.isdigit() for part in parts if part):
            value = float("".join(parts))
        else:
            return None
    if magnitude:
        value *= _MAGNITUDE[magnitude.lower()]
    return value


def _scan(text: str) -> set[float]:
    """Every figure appearing in a block of text, normalised."""
    from ..parsing.text import collapse_digit_groups

    found: set[float] = set()
    for match in _FIGURE_RE.finditer(collapse_digit_groups(text or "")):
        value = _numeric_value(match.group(1), match.group(2))
        if value is not None:
            found.add(value)
    return found


@dataclass(frozen=True)
class FactNumbers:
    """The fact set, typed. Membership is checked within type (QA D8)."""

    quantities: set[float]        # money, counts, percentages
    dates: set[tuple[int, int, int]]  # whole dates the prompt showed
    years: set[int]

    def day_month_matches(self, day: int, month: int, year: int | None) -> bool:
        return any(
            d == day and m == month and (year is None or y == year)
            for (y, m, d) in self.dates
        )


def _iso_dates(text: str) -> set[tuple[int, int, int]]:
    return {
        (int(y), int(m), int(d)) for y, m, d in _ISO_DATE_RE.findall(text or "")
    }


def fact_numbers(facts: FactSet) -> FactNumbers:
    """Everything the model was shown, split into what each figure *is*.

    **Quantities are scanned out of the rendered DATOS block** rather than
    hand-listed from `FactSet` attributes, because a hand-list drifts silently
    from what the prompt exposes — that drift was Reviewer F3, where a correct
    "el 14 de julio" was rejected because no date component was listed.

    **Dates are lifted out first and kept separately**, because the same
    widening then let a date pass as a quantity — QA D8, where "(20)" was
    accepted as a count of days only because 20 July was a top-expense date.
    A date stays sayable as a date and nothing more.
    """
    from ..parsing.text import collapse_digit_groups
    from .prompts import render_facts

    rendered = render_facts(facts)
    dates = _iso_dates(rendered)
    for boundary in (facts.period_start, facts.period_end):
        dates |= _iso_dates(boundary)

    # Quantities come from the same block with every date removed, so a date
    # component cannot enter this set through the back door.
    quantities_source = _ISO_DATE_RE.sub(" ", rendered)
    quantities: set[float] = {0.0, 100.0}
    for match in _FIGURE_RE.finditer(collapse_digit_groups(quantities_source)):
        value = _numeric_value(match.group(1), match.group(2))
        if value is not None:
            quantities.add(value)

    # The structured aggregates too, so the set never depends on rendering.
    for value in (facts.total_cop, facts.expense_count, facts.distinct_days,
                  facts.journal_entries_considered, facts.journal_entries_used):
        if value is not None:
            quantities.add(float(value))
    for item in facts.by_category or []:
        quantities.add(float(item["amount_cop"]))
        quantities.add(float(item["percent"]))
    for item in facts.by_payment_method or []:
        quantities.add(float(item["amount_cop"]))
    for item in facts.top_expenses or []:
        quantities.add(float(item["amount_cop"]))

    years = {y for (y, _m, _d) in dates}
    for token in re.findall(r"\b(\d{4})\b", facts.period_label or ""):
        years.add(int(token))
    return FactNumbers(quantities=quantities, dates=dates, years=years)


def check(text: str, facts: FactSet) -> GuardResult:
    """Every figure in `text` must be verifiable **as the kind of thing it is**."""
    from ..parsing.text import collapse_digit_groups

    numbers = fact_numbers(facts)
    body = collapse_digit_groups(text or "")
    offending: list[str] = []

    # 1. Dates, validated whole and then removed so their components cannot be
    #    re-read as quantities.
    def take_iso(match: re.Match) -> str:
        y, m, d = (int(part) for part in match.groups())
        if (y, m, d) not in numbers.dates:
            offending.append(match.group(0))
        return " "

    body = _ISO_DATE_RE.sub(take_iso, body)

    def take_spanish(match: re.Match) -> str:
        first, second, month_name, year = match.groups()
        month = _MONTHS_ES[month_name.lower()]
        year_value = int(year) if year else None
        for day in (first, second):
            if day is None:
                continue
            if not numbers.day_month_matches(int(day), month, year_value):
                offending.append(match.group(0).strip())
                break
        return " "

    body = _ES_DATE_RE.sub(take_spanish, body)

    # 2. Whatever is left is a quantity claim, and is checked against
    #    quantities alone. A bare year is allowed only if the facts carry it.
    for match in _FIGURE_RE.finditer(body):
        value = _numeric_value(match.group(1), match.group(2))
        if value is None:
            continue
        if value in numbers.quantities:
            continue
        if match.group(2) is None and float(value).is_integer() and int(value) in numbers.years:
            continue
        offending.append(match.group(0).strip())

    return GuardResult(ok=not offending, offending=offending)
