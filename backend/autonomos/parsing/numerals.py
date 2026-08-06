"""Spanish numeral grammar, 0 - 999,999,999, plus Colombian digit grouping.

2.4 and 9.6 are pass/fail criteria, so this is rules and never a model (KD-8).
Handles `14.000`, `14000`, `14 000`, `14,000`, `catorce mil`, `14 mil`,
`mil quinientos`, `un millon doscientos mil`, and mixtures of the two forms.
"""

from __future__ import annotations

import re

from .text import normalize

UNITS: dict[str, int] = {
    "cero": 0,
    "un": 1, "uno": 1, "una": 1,
    "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
    "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13,
    "catorce": 14, "quince": 15,
    "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
    "veinte": 20,
    "veintiun": 21, "veintiuno": 21, "veintiuna": 21, "veintidos": 22,
    "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26,
    "veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
    "setenta": 70, "ochenta": 80, "noventa": 90,
}

HUNDREDS: dict[str, int] = {
    "cien": 100, "ciento": 100,
    "doscientos": 200, "doscientas": 200,
    "trescientos": 300, "trescientas": 300,
    "cuatrocientos": 400, "cuatrocientas": 400,
    "quinientos": 500, "quinientas": 500,
    "seiscientos": 600, "seiscientas": 600,
    "setecientos": 700, "setecientas": 700,
    "ochocientos": 800, "ochocientas": 800,
    "novecientos": 900, "novecientas": 900,
}

MULTIPLIERS: dict[str, int] = {
    "mil": 1_000,
    "miles": 1_000,
    "millon": 1_000_000,
    "millones": 1_000_000,
}

CONNECTORS = {"y", "de"}

MAX_VALUE = 999_999_999

# `14.000` / `14 000` / `14,000` — one or more groups of exactly three digits.
_GROUPED_RE = re.compile(r"^\d{1,3}(?:[.,  ]\d{3})+$")
_PLAIN_RE = re.compile(r"^\d+$")


def spanish_number_tokens() -> set[str]:
    """Every word this grammar understands (used to find candidate spans)."""
    return set(UNITS) | set(HUNDREDS) | set(MULTIPLIERS)


def _digits_value(token: str) -> int | None:
    compact = token.replace(".", "").replace(",", "").replace(" ", "").replace(" ", "")
    if not compact.isdigit():
        return None
    return int(compact)


def parse_digit_group(text: str) -> int | None:
    """`14.000` -> 14000. Returns None when the text is not a digit amount."""
    candidate = (text or "").strip()
    if _GROUPED_RE.match(candidate) or _PLAIN_RE.match(candidate):
        return _digits_value(candidate)
    return None


def parse_spanish_number(text: str) -> int | None:
    """Resolve a Spanish/numeric amount phrase to an integer, or None.

    Words and digits may be mixed: `14 mil`, `dos mil quinientos`, `1 millon`.
    """
    words = normalize(text).split()
    if not words:
        return None

    total = 0
    current = 0
    seen_any = False
    pending_multiplier_scale = MAX_VALUE + 1  # multipliers must be strictly decreasing

    for word in words:
        if word in CONNECTORS:
            if not seen_any:
                return None
            continue

        digit_value = _digits_value(word) if word[0].isdigit() else None

        if digit_value is not None:
            if digit_value > MAX_VALUE:
                return None
            if seen_any and current != 0:
                return None  # "14 20" is not a number
            current += digit_value
            seen_any = True
            continue

        if word in UNITS:
            value = UNITS[word]
            sub = current % 100
            # `treinta y cinco` is fine; `cinco cinco` and `veinte treinta` are not.
            if sub % 10 != 0 or (value >= 10 and sub != 0):
                return None
            current += value
            seen_any = True
            continue

        if word in HUNDREDS:
            if current >= 100:
                return None
            current += HUNDREDS[word]
            seen_any = True
            continue

        if word in MULTIPLIERS:
            scale = MULTIPLIERS[word]
            if scale >= pending_multiplier_scale:
                return None  # "mil mil"
            pending_multiplier_scale = scale
            multiplicand = current if current else 1
            if multiplicand * scale > MAX_VALUE:
                return None
            total += multiplicand * scale
            current = 0
            seen_any = True
            continue

        return None  # a word this grammar does not know: not a number phrase

    if not seen_any:
        return None
    value = total + current
    return value if 0 <= value <= MAX_VALUE else None
