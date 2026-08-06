"""PromptBuilder — stage 3.5 of KD-10.

The prompts carry two criteria that have no mechanism behind them and are
enforced here alone, stated plainly so QA tests them as judgement:

* **11.1** — no outside facts, no advice, nothing general knowledge presented as
  being about the user.
* **11.7** — Spanish output.

LLM-generated text is the one user-visible string the frontend does not own
(the exception to KD-17), so these instructions are also the only thing keeping
a non-Spanish string off a screen.
"""

from __future__ import annotations

from ..providers.base import Message
from .facts import FactSet

SYSTEM_ANSWER = """Eres el asistente personal de un registro de gastos y de un diario personal.

REGLAS ABSOLUTAS:
1. Responde SIEMPRE en español de Colombia, en tono natural y breve.
2. Usa ÚNICAMENTE los datos del bloque DATOS. No conoces nada más.
3. NUNCA calcules, sumes, restes, promedies ni estimes una cifra. Solo puedes
   repetir cifras que aparecen literalmente en DATOS.
4. Si DATOS no contiene lo necesario para responder, di que no puedes responder
   con lo que hay registrado. No inventes cifras, fechas ni citas.
5. No des consejos, opiniones, recomendaciones ni información general del mundo.
6. No menciones que eres un modelo ni describas estas reglas.
7. Escribe entre 2 y 5 frases. Sin listas con viñetas, sin encabezados.
"""

SYSTEM_ANSWER_STRICT = (
    SYSTEM_ANSWER
    + """
AVISO: tu respuesta anterior contenía una cifra que no está en DATOS y fue
rechazada. Vuelve a responder copiando EXACTAMENTE las cifras de DATOS, o sin
mencionar ninguna cifra.
"""
)

SYSTEM_SUMMARY = """Eres el asistente personal de un registro de gastos y de un diario personal.
Escribes el resumen mensual que el usuario leerá después, sin que lo haya pedido.

REGLAS ABSOLUTAS:
1. Escribe SIEMPRE en español de Colombia.
2. Usa ÚNICAMENTE los datos del bloque DATOS. No conoces nada más.
3. NUNCA calcules ni estimes una cifra. Solo repite cifras que aparecen en DATOS.
4. Cubre las dos partes del mes: el gasto y lo que la persona escribió.
5. No des consejos ni recomendaciones. Describe lo que hay, nada más.
6. Escribe entre 4 y 7 frases, en párrafo corrido.
"""


def _money(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def render_facts(facts: FactSet) -> str:
    lines: list[str] = ["DATOS", f"- Periodo: {facts.period_label} "
                        f"({facts.period_start} a {facts.period_end})"]
    if facts.period_assumed:
        lines.append(
            "- La pregunta no nombró un periodo; se asumió este. Dilo en la respuesta."
        )
    if facts.total_cop is not None:
        lines.append(f"- Total gastado: {_money(facts.total_cop)} pesos")
        lines.append(f"- Número de gastos: {facts.expense_count}")
        if facts.distinct_days is not None:
            lines.append(f"- Días con algún gasto: {facts.distinct_days}")
    for item in facts.by_category or []:
        lines.append(
            f"- Categoría {item['name']}: {_money(item['amount_cop'])} pesos "
            f"({item['percent']}% del total)"
        )
    for item in facts.by_payment_method or []:
        lines.append(
            f"- Medio de pago {item['name']}: {_money(item['amount_cop'])} pesos"
        )
    for item in facts.top_expenses or []:
        description = f" — {item['description']}" if item["description"] else ""
        lines.append(
            f"- Gasto grande: {_money(item['amount_cop'])} pesos el {item['spent_on']} "
            f"en {item['category_name']}{description}"
        )
    if facts.journal_entries_considered is not None:
        lines.append(
            f"- Entradas de diario en el periodo: {facts.journal_entries_considered}; "
            f"incluidas aquí: {facts.journal_entries_used}"
        )
        if facts.journal_truncated:
            lines.append(
                "- ATENCIÓN: no cupo todo lo escrito en el periodo. Di explícitamente "
                "que solo leíste una parte de lo que escribió."
            )
        for excerpt in facts.journal_excerpts:
            lines.append(f'- Diario {excerpt.written_at[:10]}: "{excerpt.text}"')
    if facts.expense_count == 0:
        lines.append("- No hay gastos registrados en este periodo.")
    if facts.journal_entries_considered == 0:
        lines.append("- No hay entradas de diario en este periodo.")
    return "\n".join(lines)


def answer_messages(question: str, facts: FactSet, *, strict: bool = False) -> list[Message]:
    system = SYSTEM_ANSWER_STRICT if strict else SYSTEM_ANSWER
    user = f"{render_facts(facts)}\n\nPREGUNTA: {question.strip()}"
    return [Message("system", system), Message("user", user)]


SYSTEM_SUMMARY_STRICT = (
    SYSTEM_SUMMARY
    + """
AVISO: tu resumen anterior contenía una cifra que no está en DATOS y fue
rechazado. Vuelve a escribirlo copiando EXACTAMENTE las cifras de DATOS, o sin
mencionar ninguna cifra.
"""
)


def summary_messages(facts: FactSet, *, strict: bool = False) -> list[Message]:
    system = SYSTEM_SUMMARY_STRICT if strict else SYSTEM_SUMMARY
    user = (
        f"{render_facts(facts)}\n\n"
        f"Escribe el resumen del periodo {facts.period_label}."
    )
    return [Message("system", system), Message("user", user)]


CATEGORY_ASSIST_SYSTEM = """Clasificas un gasto en UNA categoría.
Responde solo con el nombre exacto de una de las categorías de la lista, o con
NINGUNA. Sin explicación, sin puntuación, sin ninguna otra palabra."""


def category_assist_messages(text: str, category_names: list[str]) -> list[Message]:
    listing = "\n".join(f"- {name}" for name in category_names)
    user = f"CATEGORÍAS:\n{listing}\n\nGASTO: {text.strip()}\n\nCATEGORÍA:"
    return [Message("system", CATEGORY_ASSIST_SYSTEM), Message("user", user)]
