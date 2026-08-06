"""Text normalisation shared by the amount grammar and the alias matcher.

Pure functions, no I/O, no model (design: `parsing/`).
"""

from __future__ import annotations

import re
import unicodedata

_PUNCT_RE = re.compile(r"[^\w\s$.,]", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+")
# A `.` or `,` that is not a Colombian thousands separator is punctuation.
_LOOSE_SEPARATOR_RE = re.compile(r"(?<!\d)[.,]|[.,](?!\d)")
# `14.000` / `14 000` / `14,000` collapse to `14000` before any parsing.
_GROUP_JOIN_RE = re.compile(r"(?<=\d)[.,  ](?=\d{3}(?!\d))")


def strip_accents(value: str) -> str:
    """`crédito` -> `credito`. Keeps ñ as n, which is what alias matching wants."""
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def collapse_digit_groups(value: str) -> str:
    """`14.000` / `14 000` / `14,000` -> `14000` (2.4)."""
    previous = None
    current = value
    while previous != current:
        previous = current
        current = _GROUP_JOIN_RE.sub("", current)
    return current


def normalize(value: str) -> str:
    """Lowercase, accent-free, punctuation-free, single-spaced.

    Thousands separators inside a number survive as joined digits; every other
    `.` and `,` becomes a space so `pesos.` tokenises as `pesos`.
    """
    lowered = strip_accents(value or "").lower()
    joined = collapse_digit_groups(lowered)
    cleaned = _LOOSE_SEPARATOR_RE.sub(" ", joined)
    cleaned = _PUNCT_RE.sub(" ", cleaned)
    cleaned = cleaned.replace("$", " ")
    return _WS_RE.sub(" ", cleaned).strip()


def tokenize(value: str) -> list[str]:
    return normalize(value).split(" ") if normalize(value) else []


def trim_on_word_boundary(value: str, limit: int) -> tuple[str, bool]:
    """Trim to `limit` characters without cutting a word in half.

    Returns `(text, truncated)`. KD-8: the draft description is the transcript
    trimmed this way; the untrimmed text always stays in `transcript`.
    """
    text = value or ""
    if len(text) <= limit:
        return text, False
    cut = text[:limit]
    space = cut.rfind(" ")
    if space > limit // 2:
        cut = cut[:space]
    return cut.rstrip(), True
