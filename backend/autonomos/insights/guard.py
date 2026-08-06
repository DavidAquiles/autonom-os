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


def allowed_values(facts: FactSet) -> set[float]:
    """The closed set of figures the model is permitted to state."""
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
    return allowed


def check(text: str, facts: FactSet) -> GuardResult:
    from ..parsing.text import collapse_digit_groups

    allowed = allowed_values(facts)
    offending: list[str] = []
    for match in _FIGURE_RE.finditer(collapse_digit_groups(text or "")):
        raw, magnitude = match.group(1), match.group(2)
        value = _numeric_value(raw, magnitude)
        if value is None:
            continue
        if value not in allowed:
            offending.append(match.group(0).strip())
    return GuardResult(ok=not offending, offending=offending)
