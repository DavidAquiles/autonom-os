"""SQLite connection setup and migration runner (KD-4).

WAL, `synchronous=FULL`, foreign keys on. One writer, one process, one worker.
The connection is per-thread; FastAPI's sync endpoints and the asyncio tasks
both reach it through `get_db()`.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..clock import now_iso
from ..config import get_settings

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

_local = threading.local()
_init_lock = threading.Lock()
_initialised_for: Path | None = None


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def get_db() -> sqlite3.Connection:
    """The calling thread's connection, initialising the schema on first use."""
    settings = get_settings()
    conn: sqlite3.Connection | None = getattr(_local, "conn", None)
    if conn is not None and getattr(_local, "path", None) == settings.db_path:
        return conn
    init_db()
    conn = connect(settings.db_path)
    _local.conn = conn
    _local.path = settings.db_path
    return conn


def close_thread_db() -> None:
    conn: sqlite3.Connection | None = getattr(_local, "conn", None)
    if conn is not None:
        conn.close()
        _local.conn = None
        _local.path = None


def reset_for_tests() -> None:
    """Drop the cached per-thread connection and the one-shot init guard."""
    global _initialised_for
    close_thread_db()
    with _init_lock:
        _initialised_for = None


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def _applied_version(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='meta'"
    ).fetchone()
    if row is None:
        return 0
    got = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    return int(got["value"]) if got else 0


def migration_files() -> list[tuple[int, Path]]:
    files = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        files.append((int(path.name.split("_", 1)[0]), path))
    return files


def schema_version() -> int:
    files = migration_files()
    return files[-1][0] if files else 0


def init_db() -> None:
    """Apply pending migrations and seed first-run data. Idempotent."""
    global _initialised_for
    settings = get_settings()
    with _init_lock:
        if _initialised_for == settings.db_path:
            return
        conn = connect(settings.db_path)
        try:
            current = _applied_version(conn)
            for version, path in migration_files():
                if version <= current:
                    continue
                conn.executescript(path.read_text(encoding="utf-8"))
                conn.execute(
                    "INSERT INTO meta(key, value) VALUES('schema_version', ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (str(version),),
                )
                current = version
            conn.execute(
                "INSERT INTO meta(key, value) VALUES('initialised_at', ?) "
                "ON CONFLICT(key) DO NOTHING",
                (now_iso(),),
            )
            from .seed import seed_if_empty

            seed_if_empty(conn)
        finally:
            conn.close()
        _initialised_for = settings.db_path
