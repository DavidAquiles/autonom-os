"""Live integration check against the real sidecars. Not part of the test suite.

    .venv/bin/python tools/live_check.py llm
    .venv/bin/python tools/live_check.py stt   # needs whisper-server on :8081

Exercises the real providers, the arbiter and the job runner, and prints the
`elapsed_ms` figures R9 asks to be logged from day one.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("DB_PATH", str(Path.home() / ".cache" / "autonomos-live.db"))
os.environ.setdefault("SNAPSHOT_DIR", str(Path.home() / ".cache" / "autonomos-live-snap"))
os.environ.setdefault("SCHEDULER_ENABLED", "0")

from autonomos.clock import now_iso, today_str  # noqa: E402
from autonomos.db import get_db  # noqa: E402
from autonomos.insights import runner  # noqa: E402
from autonomos.providers import get_llm, get_stt  # noqa: E402
from autonomos.repo import jobs as jobs_repo  # noqa: E402


def seed() -> None:
    conn = get_db()
    conn.execute("DELETE FROM expenses")
    conn.execute("DELETE FROM journal_entries")
    ts = now_iso()
    rows = [(14000, 2, 2, "Uber al centro"), (32000, 1, 1, "Almuerzo"), (54000, 3, 4, "Mercado")]
    for amount, category, method, description in rows:
        conn.execute(
            "INSERT INTO expenses(amount_cop, category_id, payment_method_id, spent_on,"
            " description, source, created_at, updated_at) VALUES(?,?,?,?,?,'manual',?,?)",
            (amount, category, method, today_str(), description, ts, ts),
        )
    conn.execute(
        "INSERT INTO journal_entries(text, written_at, source, created_at, updated_at)"
        " VALUES(?,?,'manual',?,?)",
        ("Hoy estuve pensando en cuánto se me va en transporte.", ts, ts, ts),
    )


async def check_llm() -> None:
    llm = get_llm()
    print("llm health:", await llm.health())
    seed()
    conn = get_db()
    for question in (
        "¿cuánto gasté hoy?",
        "¿en qué categoría se me fue más plata este mes?",
        "¿qué escribí en el diario este mes?",
    ):
        row = jobs_repo.create(conn, question, "text")
        started = time.monotonic()
        await runner._run_question(row["id"], question, asyncio.Event())
        elapsed = time.monotonic() - started
        final = jobs_repo.get(conn, row["id"])
        print(f"\nQ: {question}\n  {elapsed:6.1f}s  status={final['status']} "
              f"error={final['error_code']}\n  A: {final['answer']}")


async def check_stt() -> None:
    from tests.conftest import wav_bytes

    stt = get_stt()
    print("stt health:", await stt.health())
    started = time.monotonic()
    result = await stt.transcribe(wav_bytes(4.0), language="es", timeout_s=30)
    print(f"transcribe round trip: {time.monotonic() - started:.1f}s "
          f"no_speech={result.no_speech} text={result.text!r}")


async def check_contention(sample: Path) -> None:
    """KD-12 against both real runtimes: a transcription must preempt a running
    question, and the question must terminate as `preempted`."""
    from autonomos.arbiter import JobKind, get_arbiter

    seed()
    conn = get_db()
    question = "¿en qué categoría se me fue más plata este mes y qué escribí?"
    row = jobs_repo.create(conn, question, "text")
    task = asyncio.ensure_future(runner._run_question(row["id"], question, asyncio.Event()))
    await asyncio.sleep(float(sys.argv[3]) if len(sys.argv) > 3 else 6.0)

    started = time.monotonic()
    cancel = asyncio.Event()
    lease = await get_arbiter().acquire(JobKind.TRANSCRIPTION, cancel, wait_timeout_s=20)
    try:
        result = await get_stt().transcribe(
            sample.read_bytes(), language="es", timeout_s=20
        )
    finally:
        get_arbiter().release(lease)
    print(f"transcription took {time.monotonic() - started:.1f}s -> {result.text!r}")

    await asyncio.wait_for(task, 30)
    final = jobs_repo.get(conn, row["id"])
    print(f"question ended: status={final['status']} error={final['error_code']} "
          f"partial(diagnostics only, not on the wire)="
          f"{(final['partial_answer'] or '')[:60]!r}")


def check_endpoint(sample: Path) -> None:
    """The whole endpoint against the real sidecar, with a real WAV file."""
    from fastapi.testclient import TestClient

    from autonomos.main import create_app

    with TestClient(create_app()) as client:
        for context in ("expense", "journal"):
            started = time.monotonic()
            response = client.post(
                "/api/voice/transcribe",
                files={"audio": (sample.name, sample.read_bytes(), "audio/wav")},
                data={"context": context},
            )
            print(f"{context}: {response.status_code} in "
                  f"{time.monotonic() - started:.1f}s -> {response.json()}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "llm"
    if target == "contention":
        asyncio.run(check_contention(Path(sys.argv[2])))
    elif target == "endpoint":
        check_endpoint(Path(sys.argv[2]))
    else:
        asyncio.run(check_llm() if target == "llm" else check_stt())
