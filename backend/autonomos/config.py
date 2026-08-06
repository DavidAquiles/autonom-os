"""Runtime configuration, read once from the environment.

Every value named in KD-7 keeps the exact env-var name the design gives it, so a
provider swap really is a config change (`LLM_BASE_URL`, `LLM_MODEL`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return default if value is None or value == "" else value


def _env_first(names: tuple[str, ...], default: str) -> str:
    """First of several accepted names that is set. Later names are legacy."""
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)))
    except ValueError:
        return default


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    if not raw:
        return default
    p = Path(raw).expanduser()
    return p if p.is_absolute() else (REPO_ROOT / p)


@dataclass(frozen=True)
class Settings:
    # --- general -----------------------------------------------------------
    app_tz: str = field(default_factory=lambda: _env("APP_TZ", "America/Bogota"))
    version: str = field(default_factory=lambda: _env("APP_VERSION", "0.1.0"))

    # --- storage -----------------------------------------------------------
    db_path: Path = field(
        default_factory=lambda: _env_path("DB_PATH", REPO_ROOT / "data" / "autonomos.db")
    )
    snapshot_dir: Path = field(
        default_factory=lambda: _env_path(
            "SNAPSHOT_DIR", REPO_ROOT / "data" / "snapshots"
        )
    )
    snapshot_keep_days: int = field(
        default_factory=lambda: _env_int("SNAPSHOT_KEEP_DAYS", 7)
    )

    # --- listeners (KD-2) ---------------------------------------------------
    # The loopback port `tailscale serve` points at. Default 8001, not 8000:
    # 8000 is permanently held on this host by an unrelated Docker container
    # (`trace_erp_api`, published on all interfaces), so a default of 8000 would
    # crash-loop the unit on the one machine this app runs on. Configurable —
    # the point is that the default works here.
    api_host: str = field(
        default_factory=lambda: _env_first(("AUTONOMOS_API_HOST", "API_HOST"), "127.0.0.1")
    )
    api_port: int = field(
        default_factory=lambda: int(
            _env_first(("AUTONOMOS_API_PORT", "API_PORT"), "8001")
        )
    )
    # The LAN fallback binds ONE named interface and is never 0.0.0.0. Unset it
    # on any network David does not control — it is unauthenticated by A6.
    lan_bind_addr: str = field(default_factory=lambda: _env("LAN_BIND_ADDR", ""))
    lan_port: int = field(default_factory=lambda: _env_int("LAN_PORT", 8443))
    tls_certfile: str = field(default_factory=lambda: _env("TLS_CERTFILE", ""))
    tls_keyfile: str = field(default_factory=lambda: _env("TLS_KEYFILE", ""))

    # --- static SPA --------------------------------------------------------
    frontend_dist: Path = field(
        default_factory=lambda: _env_path(
            "FRONTEND_DIST", REPO_ROOT / "frontend" / "dist"
        )
    )

    # --- LLM (KD-7) --------------------------------------------------------
    llm_provider: str = field(
        default_factory=lambda: _env("LLM_PROVIDER", "openai_compatible")
    )
    llm_base_url: str = field(
        default_factory=lambda: _env("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    )
    llm_model: str = field(
        default_factory=lambda: _env("LLM_MODEL", "qwen2.5:3b-instruct-q4_K_M")
    )
    llm_deadline_answer_s: float = field(
        default_factory=lambda: _env_float("LLM_DEADLINE_ANSWER_S", 110.0)
    )
    llm_min_start_budget_s: float = field(
        default_factory=lambda: _env_float("LLM_MIN_START_BUDGET_S", 30.0)
    )
    llm_timeout_summary_s: float = field(
        default_factory=lambda: _env_float("LLM_TIMEOUT_SUMMARY_S", 300.0)
    )
    llm_max_tokens_answer: int = field(
        default_factory=lambda: _env_int("LLM_MAX_TOKENS_ANSWER", 220)
    )
    llm_max_tokens_summary: int = field(
        default_factory=lambda: _env_int("LLM_MAX_TOKENS_SUMMARY", 320)
    )

    # --- transcription (KD-7) ---------------------------------------------
    stt_provider: str = field(
        default_factory=lambda: _env("STT_PROVIDER", "whispercpp_http")
    )
    stt_base_url: str = field(
        default_factory=lambda: _env("STT_BASE_URL", "http://127.0.0.1:8081")
    )
    stt_model: str = field(default_factory=lambda: _env("STT_MODEL", "small"))
    stt_timeout_s: float = field(default_factory=lambda: _env_float("STT_TIMEOUT_S", 20.0))
    stt_language: str = field(default_factory=lambda: _env("STT_LANGUAGE", "es"))
    max_audio_s: float = field(default_factory=lambda: _env_float("MAX_AUDIO_S", 32.0))
    max_audio_bytes: int = field(
        default_factory=lambda: _env_int("MAX_AUDIO_BYTES", 2 * 1024 * 1024)
    )
    min_audio_s: float = field(default_factory=lambda: _env_float("MIN_AUDIO_S", 0.4))

    # --- category assist (KD-8 layer 2) ------------------------------------
    assist_timeout_s: float = field(
        default_factory=lambda: _env_float("ASSIST_TIMEOUT_S", 6.0)
    )
    assist_max_tokens: int = field(
        default_factory=lambda: _env_int("ASSIST_MAX_TOKENS", 8)
    )

    # --- arbiter / scheduler (KD-12) ---------------------------------------
    arbiter_quiet_period_s: float = field(
        default_factory=lambda: _env_float("ARBITER_QUIET_PERIOD_S", 60.0)
    )
    arbiter_preempt_grace_s: float = field(
        default_factory=lambda: _env_float("ARBITER_PREEMPT_GRACE_S", 2.0)
    )
    scheduler_tick_s: float = field(
        default_factory=lambda: _env_float("SCHEDULER_TICK_S", 900.0)
    )
    scheduler_enabled: bool = field(
        default_factory=lambda: _env("SCHEDULER_ENABLED", "1") not in ("0", "false")
    )
    summary_max_attempts: int = field(
        default_factory=lambda: _env_int("SUMMARY_MAX_ATTEMPTS", 3)
    )

    # --- insights ----------------------------------------------------------
    journal_context_tokens: int = field(
        default_factory=lambda: _env_int("JOURNAL_CONTEXT_TOKENS", 1200)
    )
    status_cache_s: float = field(default_factory=lambda: _env_float("STATUS_CACHE_S", 30.0))


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Test seam: force a re-read of the environment."""
    global _settings
    _settings = None
