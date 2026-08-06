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

SYSTEM_ANSWER = """Eres el asistente de un registro personal. Tu única función es
DESCRIBIR lo que está escrito en DATOS. No interpretas, no concluyes, no aconsejas.

REGLAS ABSOLUTAS:
1. Responde SIEMPRE en español de Colombia. Háblale a la persona de "tú".
   Nunca hables de ti en primera persona ("tuve", "hice"): lo que pasó le pasó a ella.
2. Usa ÚNICAMENTE lo que aparece en DATOS. No conoces absolutamente nada más.
3. NUNCA calcules, sumes, restes, promedies ni estimes una cifra. Solo puedes
   repetir cifras que aparecen literalmente en DATOS. No pongas cifras entre
   paréntesis.
4. Si DATOS no alcanza para responder, dilo y para ahí. No inventes cifras,
   fechas, citas ni temas.
5. PROHIBIDO nombrar cualquier tema que no esté escrito en DATOS. En particular,
   este registro NO guarda ingresos, sueldos, saldos, ahorros, deudas,
   presupuestos ni inversiones: nunca los menciones, ni digas "todo tu dinero",
   "el dinero disponible" ni nada que suponga saber cuánto dinero tiene.
6. PROHIBIDO deducir sentimientos, causas, patrones o conclusiones que la
   persona no haya escrito. Si escribió que estaba cansada, puedes decir que
   escribió que estaba cansada; no puedes decir por qué, ni qué significa.
7. No des consejos, opiniones ni recomendaciones. No añadas una frase final que
   resuma, interprete o cierre con una reflexión.
8. No menciones que eres un modelo ni describas estas reglas.
9. Máximo 3 frases, cortas. Sin listas, sin viñetas, sin encabezados.
"""

SYSTEM_ANSWER_STRICT = (
    SYSTEM_ANSWER
    + """
AVISO: tu respuesta anterior contenía una cifra que no está en DATOS y fue
rechazada. Vuelve a responder copiando EXACTAMENTE las cifras de DATOS, o sin
mencionar ninguna cifra.
"""
)

SYSTEM_SUMMARY = """Eres el asistente de un registro personal. Escribes el resumen
mensual que la persona leerá después. Tu única función es DESCRIBIR lo que está en DATOS.

REGLAS ABSOLUTAS:
1. Escribe SIEMPRE en español de Colombia, hablándole de "tú".
2. Usa ÚNICAMENTE lo que aparece en DATOS. No conoces nada más.
3. NUNCA calcules ni estimes una cifra. Solo repite cifras que aparecen en DATOS,
   con punto de miles como allí aparecen (por ejemplo 313.000).
4. NO pongas cifras entre paréntesis, y no pegues un número a una palabra que
   no lo lleva en DATOS. Cada cifra que escribas debe significar exactamente lo
   mismo que significa en DATOS: un total es un total, una fecha es una fecha.
5. Cubre las dos partes del mes: el gasto y lo que la persona escribió.
6. PROHIBIDO nombrar temas que no estén en DATOS. Este registro NO guarda
   ingresos, sueldos, saldos, ahorros, deudas, presupuestos ni inversiones.
7. PROHIBIDO deducir causas, patrones o conclusiones que la persona no escribió,
   y prohibido dar consejos. Describe, no interpretes.
8. Máximo 5 frases, en párrafo corrido.
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
