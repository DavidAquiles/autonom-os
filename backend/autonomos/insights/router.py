"""QuestionRouter — stage 1 of KD-10. Rules, never a model.

Resolves the period and the domain from Spanish. **A period it cannot resolve
is a failure, not a default**: if a temporal cue is present but nothing
resolves, the job terminates with `period_unrecognised`. Only a question with
no temporal cue at all falls back to the current month, and then
`facts.period_assumed` is true so the answer can label itself.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from ..clock import (
    MONTH_NAMES_ES,
    month_bounds,
    month_key_of,
    previous_month,
    today,
    week_bounds,
)
from ..parsing.text import normalize

MONTH_INDEX = {normalize(name): i + 1 for i, name in enumerate(MONTH_NAMES_ES)}
MONTH_INDEX["setiembre"] = 9

# A cue says "this question is about a period"; failing to resolve one is an
# error rather than a silent fallback (KD-10).
TEMPORAL_CUE_WORDS = {
    "semana", "semanas", "mes", "meses", "ano", "anos", "dia", "dias",
    "quincena", "quincenas", "trimestre", "trimestres", "desde", "hasta",
    "ultimos", "ultimas", "ultimo", "ultima", "pasado", "pasada", "anterior",
    "anteriores", "hoy", "ayer", "anteayer", "fin de semana", "semestre",
    "temporada", "periodo",
}
TEMPORAL_CUE_WORDS |= set(MONTH_INDEX.keys())

_YEAR_RE = re.compile(r"\b(20\d\d)\b")

FINANCE_WORDS = {
    "gaste", "gasto", "gastos", "gastar", "gastado", "plata", "dinero", "pesos",
    "peso", "pago", "pague", "pagos", "compra", "compras", "compre", "tarjeta",
    "efectivo", "categoria", "categorias", "presupuesto", "factura", "costo",
    "costos", "gastando", "invertido", "salida de dinero", "metodo de pago",
}
JOURNAL_WORDS = {
    "diario", "escribi", "escrito", "entrada", "entradas", "pensaba", "pense",
    "preocupaba", "preocupa", "sentia", "senti", "animo", "humor", "notas",
    "nota", "reflexion", "reflexiones", "emociones", "triste", "feliz",
    "ansiedad", "sueno", "suenos", "escribiendo", "conte", "pensamientos",
}


class PeriodUnrecognised(Exception):
    """A temporal cue was present and no period could be resolved (11.11)."""


@dataclass(frozen=True)
class Route:
    period_start: str
    period_end: str
    period_label: str
    period_assumed: bool
    domain: str  # "finances" | "journal" | "both"


def has_temporal_cue(text: str) -> bool:
    tokens = set(normalize(text).split())
    if tokens & TEMPORAL_CUE_WORDS:
        return True
    return bool(_YEAR_RE.search(text or ""))


def resolve_domain(conn: sqlite3.Connection | None, text: str) -> str:
    tokens = set(normalize(text).split())
    finance_terms = set(FINANCE_WORDS)
    if conn is not None:
        for row in conn.execute(
            "SELECT name FROM categories UNION SELECT name FROM payment_methods"
        ).fetchall():
            finance_terms.update(normalize(row["name"]).split())
    finance = bool(tokens & finance_terms)
    journal = bool(tokens & JOURNAL_WORDS)
    if finance and not journal:
        return "finances"
    if journal and not finance:
        return "journal"
    return "both"  # both, or neither


def _month_range(month_key: str) -> tuple[str, str, str]:
    start, end = month_bounds(month_key)
    year, mon = (int(p) for p in month_key.split("-"))
    return start, end, f"{MONTH_NAMES_ES[mon - 1]} de {year}"


def resolve_period(text: str, reference: date | None = None) -> tuple[str, str, str] | None:
    """`(start, end, label)` or None when nothing resolves."""
    ref = reference or today()
    norm = f" {normalize(text)} "

    def has(phrase: str) -> bool:
        return f" {phrase} " in norm

    if has("hoy"):
        return ref.isoformat(), ref.isoformat(), "hoy"
    if has("ayer"):
        day = ref - timedelta(days=1)
        return day.isoformat(), day.isoformat(), "ayer"
    if has("anteayer") or has("antier"):
        day = ref - timedelta(days=2)
        return day.isoformat(), day.isoformat(), "anteayer"

    if has("esta semana"):
        start, end = week_bounds(ref)
        return start, end, "esta semana"
    if has("semana pasada") or has("la semana anterior"):
        start, end = week_bounds(ref - timedelta(days=7))
        return start, end, "la semana pasada"

    if has("este mes") or has("el mes actual"):
        start, end, _label = _month_range(month_key_of(ref))
        return start, end, _label
    if has("mes pasado") or has("el mes anterior"):
        start, end, label = _month_range(previous_month(month_key_of(ref)))
        return start, end, label

    if has("este ano") or has("el ano actual"):
        return f"{ref.year}-01-01", f"{ref.year}-12-31", str(ref.year)
    if has("ano pasado") or has("el ano anterior"):
        return f"{ref.year - 1}-01-01", f"{ref.year - 1}-12-31", str(ref.year - 1)

    year_match = _YEAR_RE.search(text or "")
    tokens = normalize(text).split()
    for index, token in enumerate(tokens):
        if token in MONTH_INDEX:
            month_number = MONTH_INDEX[token]
            year = int(year_match.group(1)) if year_match else ref.year
            if not year_match and (year, month_number) > (ref.year, ref.month):
                year -= 1  # "julio" said in March means last July
            _ = index
            start, end, label = _month_range(f"{year}-{month_number:02d}")
            return start, end, label

    if year_match:
        year = int(year_match.group(1))
        return f"{year}-01-01", f"{year}-12-31", str(year)

    return None


def route(conn: sqlite3.Connection | None, question: str, reference: date | None = None) -> Route:
    resolved = resolve_period(question, reference)
    domain = resolve_domain(conn, question)
    if resolved is None:
        if has_temporal_cue(question):
            # Answering about a different period would be exactly the
            # fabrication 11.11 forbids, and NumericGuard cannot see it.
            raise PeriodUnrecognised(question)
        ref = reference or today()
        start, end, label = _month_range(month_key_of(ref))
        return Route(start, end, label, True, domain)
    start, end, label = resolved
    return Route(start, end, label, False, domain)
