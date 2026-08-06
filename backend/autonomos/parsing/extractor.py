"""Layer 1 of KD-8: the deterministic Spanish expense extractor.

Sub-millisecond, no model. It fills amount, payment method, category and
description from a transcript; anything it cannot determine it leaves null and
marks `resolved_by.<field> == "none"` (9.2) rather than guessing.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field

from .aliases import Target, category_vocabulary, payment_method_vocabulary
from .numerals import MULTIPLIERS, parse_spanish_number, spanish_number_tokens
from .text import normalize, trim_on_word_boundary

DESCRIPTION_LIMIT = 1000

# Cue words that make a number an *amount* rather than a time or a count.
SPEND_VERBS = {
    "gaste", "gasto", "gastamos", "gastando", "pague", "pago", "pagando",
    "costo", "cuesta", "valio", "vale", "compre", "compro", "salio", "sale",
    "invertí", "inverti", "me", "por",
}
MONEY_WORDS = {"peso", "pesos", "luca", "lucas", "barras", "cop", "signopeso"}
TIME_CUES = {"las", "la", "hora", "horas", "am", "pm"}
MONTH_WORDS = {
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
    "septiembre", "setiembre", "octubre", "noviembre", "diciembre",
}

_NUMBER_WORDS = spanish_number_tokens()
_DIGIT_RE = re.compile(r"^\d+$")


@dataclass
class ExpenseDraftData:
    """The `ExpenseDraft` of the Interface Contract, before serialisation."""

    amount_cop: int | None = None
    category_id: int | None = None
    category_name: str | None = None
    payment_method_id: int | None = None
    payment_method_name: str | None = None
    description: str = ""
    description_truncated: bool = False
    resolved_by: dict[str, str] = field(
        default_factory=lambda: {"amount": "none", "category": "none", "payment_method": "none"}
    )


@dataclass
class AmountCandidate:
    value: int
    score: int
    start: int
    end: int


def _is_number_token(token: str) -> bool:
    return token in _NUMBER_WORDS or bool(_DIGIT_RE.match(token))


def amount_candidates(text: str) -> list[AmountCandidate]:
    """Every span of the transcript that reads as a number, with a cue score."""
    tokens = normalize(text.replace("$", " signopeso ")).split()
    candidates: list[AmountCandidate] = []
    i = 0
    while i < len(tokens):
        if not _is_number_token(tokens[i]):
            i += 1
            continue
        # Longest span starting here that still parses as one number.
        best: tuple[int, int] | None = None
        j = i
        while j < len(tokens):
            token = tokens[j]
            if not (_is_number_token(token) or token in ("y", "de")):
                break
            if token in ("y", "de") and (j + 1 >= len(tokens) or not _is_number_token(tokens[j + 1])):
                break
            value = parse_spanish_number(" ".join(tokens[i : j + 1]))
            if value is not None:
                best = (value, j + 1)
            j += 1
        if best is None:
            i += 1
            continue
        value, end = best
        candidates.append(
            AmountCandidate(value=value, score=_score(tokens, i, end, value), start=i, end=end)
        )
        i = end
    return candidates


def _score(tokens: list[str], start: int, end: int, value: int) -> int:
    span = tokens[start:end]
    before = tokens[max(0, start - 3) : start]
    after = tokens[end : end + 2]
    score = 0
    magnitude = any(word in MULTIPLIERS for word in span)
    money_suffix = bool(after) and after[0] in MONEY_WORDS
    money_prefix = bool(before) and before[-1] == "signopeso"
    if magnitude:
        score += 3
    if value >= 1000:
        score += 3
    if money_suffix:
        score += 2
    if money_prefix:
        score += 3
    # Verb proximity only rescues a number carrying no money marker of its own.
    # Letting it break a tie between two marked amounts would turn 9.2's
    # "leave it empty" into a guess about which one the user meant.
    if not (magnitude or money_suffix or money_prefix or value >= 1000):
        if any(word in SPEND_VERBS for word in before):
            score += 2
    if before and before[-1] in TIME_CUES:
        score -= 4
    if after and after[0] in MONTH_WORDS:
        score -= 4
    if len(after) > 1 and after[0] == "de" and after[1] in MONTH_WORDS:
        score -= 4
    if value < 100:
        score -= 1  # a bare small number is more often a count than a price
    return score


def resolve_amount(text: str) -> int | None:
    """The single best amount, or None when two candidates tie (9.2)."""
    candidates = amount_candidates(text)
    if not candidates:
        return None
    top = max(c.score for c in candidates)
    winners = {c.value for c in candidates if c.score == top}
    if len(winners) != 1:
        return None
    value = winners.pop()
    return value if value > 0 else None


def parse_expense_text(conn: sqlite3.Connection, text: str) -> ExpenseDraftData:
    """Rules-only draft from a transcript. No model, no I/O beyond the vocabularies."""
    draft = ExpenseDraftData()

    amount = resolve_amount(text)
    if amount is not None:
        draft.amount_cop = amount
        draft.resolved_by["amount"] = "rules"

    method: Target | None = payment_method_vocabulary(conn).match(text)
    if method is not None:
        draft.payment_method_id = method.id
        draft.payment_method_name = method.name
        draft.resolved_by["payment_method"] = "rules"

    category: Target | None = category_vocabulary(conn).match(text)
    if category is not None:
        draft.category_id = category.id
        draft.category_name = category.name
        draft.resolved_by["category"] = "rules"

    description, truncated = trim_on_word_boundary((text or "").strip(), DESCRIPTION_LIMIT)
    draft.description = description
    draft.description_truncated = truncated
    return draft


def build_draft(conn: sqlite3.Connection, transcript: str) -> ExpenseDraftData:
    return parse_expense_text(conn, transcript)
