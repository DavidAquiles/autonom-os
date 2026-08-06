"""Provider selection at startup from config (KD-7)."""

from __future__ import annotations

from ..config import get_settings
from .base import (  # noqa: F401
    LLMProvider,
    Message,
    ProviderCancelled,
    ProviderTimeout,
    ProviderUnavailable,
    Transcript,
    TranscriptionProvider,
)

_llm: LLMProvider | None = None
_stt: TranscriptionProvider | None = None


def get_llm() -> LLMProvider:
    global _llm
    if _llm is None:
        settings = get_settings()
        if settings.llm_provider != "openai_compatible":
            raise RuntimeError(f"unknown LLM_PROVIDER: {settings.llm_provider}")
        from .openai_compatible import OpenAICompatibleLLM

        _llm = OpenAICompatibleLLM(settings.llm_base_url, settings.llm_model)
    return _llm


def get_stt() -> TranscriptionProvider:
    global _stt
    if _stt is None:
        settings = get_settings()
        if settings.stt_provider != "whispercpp_http":
            raise RuntimeError(f"unknown STT_PROVIDER: {settings.stt_provider}")
        from .whispercpp_http import WhisperCppHttp

        _stt = WhisperCppHttp(settings.stt_base_url)
    return _stt


def set_providers(
    llm: LLMProvider | None = None, stt: TranscriptionProvider | None = None
) -> None:
    """Test seam: install fakes without touching any caller."""
    global _llm, _stt
    _llm = llm
    _stt = stt
