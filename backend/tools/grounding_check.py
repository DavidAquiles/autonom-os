"""Measure 11.1 grounding by repetition, against the real model.

QA defect D2: asked one journal question seven times against five real entries,
**three answers appended a clause supported by nothing** — "ingresos vs
desembolsos semanales" (this app records no income at all), "Inversión en la
inversión futura", "el miedo a perder dinero". A single clean run proves
nothing here, which is why this runs N times and reports the rate.

    .venv/bin/python tools/grounding_check.py [runs]

Prints each answer and flags any content word that appears in no journal entry
and in no fact line — a crude but honest detector: it over-flags (connectives,
paraphrase) so the *answers themselves* are printed for judgement. The number to
compare across prompt versions is the count of runs a human reads as ungrounded.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("DB_PATH", str(Path.home() / ".cache" / "autonomos-ground.db"))
os.environ.setdefault("SNAPSHOT_DIR", str(Path.home() / ".cache" / "autonomos-ground-snap"))
os.environ.setdefault("SCHEDULER_ENABLED", "0")

from autonomos.clock import now_iso, today_str  # noqa: E402
from autonomos.db import get_db  # noqa: E402
from autonomos.insights import runner  # noqa: E402
from autonomos.repo import jobs as jobs_repo  # noqa: E402

QUESTION = os.environ.get("Q", "¿qué me ha preocupado este mes?")

# Five entries in the spirit of QA's fixture: ordinary life, no finance anxiety,
# no income, no investments. Anything about money worry in an answer is invented.
ENTRIES = [
    "Hoy fui al mercado y me demoré más de lo que pensaba. La fila estaba larguísima "
    "y salí de mal genio, aunque después se me pasó caminando de vuelta.",
    "Salí a caminar por el parque en la tarde. Me hizo bien despejarme un rato, "
    "venía con la cabeza llena de cosas del trabajo y no lograba soltarlas.",
    "Hablé con mi mamá un buen rato por teléfono. Me contó del jardín y de la vecina. "
    "Me quedé pensando en que la llamo menos de lo que debería.",
    "Estuve leyendo antes de dormir y me quedé dando vueltas con lo del lunes. "
    "No sé si estoy cansado o si de verdad me está pesando.",
    "El almuerzo con Andrés estuvo bueno. Hacía rato no nos veíamos y me di cuenta "
    "de que he estado bastante encerrado estos meses.",
]

# Themes the record does not contain. Their appearance is the D2 failure.
UNGROUNDED_MARKERS = [
    # QA D2's own observed inventions…
    "ingreso", "desembolso", "inversión", "inversion", "invertir",
    "ahorro", "ahorrar", "deuda", "presupuesto", "miedo a perder",
    "rentabilidad", "capital", "financier",
    # …plus the ones this harness observed: claims that presuppose a balance,
    # which this app records nowhere at all (Non-Goal 2).
    "todo tu dinero", "todo el dinero", "dinero disponible", "disponible",
    "te queda", "te quedan", "saldo",
]


LEGACY_SYSTEM_ANSWER = """Eres el asistente personal de un registro de gastos y de un diario personal.

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


def use_legacy_prompt() -> None:
    """Restore the pre-D2 prompt so the two can be compared on one fixture."""
    from autonomos.insights import prompts

    prompts.SYSTEM_ANSWER = LEGACY_SYSTEM_ANSWER
    prompts.SYSTEM_ANSWER_STRICT = LEGACY_SYSTEM_ANSWER


def seed() -> None:
    conn = get_db()
    conn.execute("DELETE FROM journal_entries")
    conn.execute("DELETE FROM expenses")
    ts = now_iso()
    for index, text in enumerate(ENTRIES):
        stamp = f"{today_str()}T{9 + index:02d}:30:00.000-05:00"
        conn.execute(
            "INSERT INTO journal_entries(text, written_at, source, created_at, updated_at)"
            " VALUES(?,?,'manual',?,?)",
            (text, stamp, ts, ts),
        )
    # A realistic month: several expenses across categories. A single-expense
    # fixture renders "100% del total", which the model verbalises as "todo tu
    # dinero" — an artefact of the fixture, not of the prompt.
    for amount, category, method, description in (
        (32000, 1, 1, "Almuerzo con Andrés"),
        (14000, 2, 2, "Uber al centro"),
        (86000, 3, 2, "Mercado de la semana"),
        (23000, 1, 1, "Café y panadería"),
    ):
        conn.execute(
            "INSERT INTO expenses(amount_cop, category_id, payment_method_id, spent_on,"
            " description, source, created_at, updated_at) VALUES(?,?,?,?,?,'manual',?,?)",
            (amount, category, method, today_str(), description, ts, ts),
        )


async def main(runs: int) -> None:
    if os.environ.get("PROMPT") == "legacy":
        use_legacy_prompt()
        print("using the LEGACY (pre-D2) prompt")
    seed()
    conn = get_db()
    flagged = 0
    for index in range(1, runs + 1):
        conn.execute("DELETE FROM insight_jobs")
        row = jobs_repo.create(conn, QUESTION, "text")
        started = time.monotonic()
        await runner._run_question(row["id"], QUESTION, asyncio.Event())
        final = jobs_repo.get(conn, row["id"])
        answer = final["answer"] or f"<{final['status']}: {final['error_code']}>"
        markers = [m for m in UNGROUNDED_MARKERS if m in answer.lower()]
        if markers:
            flagged += 1
        print(f"\n--- run {index}  {time.monotonic() - started:5.1f}s  "
              f"{'UNGROUNDED ' + str(markers) if markers else 'ok'}")
        print(f"    {answer}")
    print(f"\n=== {flagged}/{runs} runs contained an off-record money/finance theme")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 7))
