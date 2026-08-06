"""NumericGuard — stage 4 of KD-10.

Every numeric token in generated text must appear in the fact set after
normalisation. A figure that does not is a hallucination, and 11.2 makes that a
defect rather than a quirk. On violation the runner retries once with a stricter
prompt and then fails explicitly with `unverifiable_figures`.

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


def allowed_values(facts: FactSet) -> set[float]:
    """The closed set of figures the model is permitted to state.

    **Defined as: the numbers the model was actually shown.** The set is scanned
    out of the rendered DATOS block itself rather than hand-listed from
    `FactSet` attributes, because a hand-listed set drifts from what the prompt
    exposes and the drift is silent. It had already happened: `render_facts`
    writes a top expense as `... el 2025-07-14 ...` and a journal excerpt as
    `- Diario 2025-07-14: "..."`, and rule 3 of the system prompt authorises
    repeating any figure in DATOS — but the old set held no date components, so
    a correct answer saying "el 14 de julio" was rejected, burned the retry and
    terminated `unverifiable_figures` about a question answered correctly.

    This does not weaken the core property. KD-10 stage 4 defines the rule as
    membership in *the fact set*, and DATOS **is** the fact set: every line of
    it comes from a SQL aggregate or from the user's own stored text, so every
    figure in it is something the user can verify. A total the data does not
    support, a computed average, an invented percentage — none of them appear
    in DATOS, and all are still caught.
    """
    from .prompts import render_facts

    allowed: set[float] = {0.0, 100.0}
    if facts.total_cop is not None:
        allowed.add(float(facts.total_cop))
    if facts.expense_count is not None:
        allowed.add(float(facts.expense_count))
    if facts.distinct_days is not None:
        allowed.add(float(facts.distinct_days))
    for item in facts.by_category or []:
        allowed.add(float(item["amount_cop"]))
        allowed.add(float(item["percent"]))
    for item in facts.by_payment_method or []:
        allowed.add(float(item["amount_cop"]))
    for item in facts.top_expenses or []:
        allowed.add(float(item["amount_cop"]))
    for count in (facts.journal_entries_considered, facts.journal_entries_used):
        if count is not None:
            allowed.add(float(count))
    # The period itself: a date component in the answer is verifiable.
    for boundary in (facts.period_start, facts.period_end):
        year, month, day = (int(part) for part in boundary.split("-"))
        allowed.update({float(year), float(month), float(day)})
    for token in re.findall(r"\d+", facts.period_label or ""):
        allowed.add(float(token))

    # …and everything else the prompt puts in front of the model: top-expense
    # dates, journal-excerpt dates, and digits inside the user's own
    # descriptions and entries. One source, so the two modules cannot drift.
    allowed |= _scan(render_facts(facts))
    return allowed


def check(text: str, facts: FactSet) -> GuardResult:
    allowed = allowed_values(facts)
    offending: list[str] = []
    for value, token in _figures_with_tokens(text):
        if value not in allowed:
            offending.append(token)
    return GuardResult(ok=not offending, offending=offending)


def _figures_with_tokens(text: str) -> list[tuple[float, str]]:
    from ..parsing.text import collapse_digit_groups

    figures: list[tuple[float, str]] = []
    for match in _FIGURE_RE.finditer(collapse_digit_groups(text or "")):
        value = _numeric_value(match.group(1), match.group(2))
        if value is not None:
            figures.append((value, match.group(0).strip()))
    return figures
