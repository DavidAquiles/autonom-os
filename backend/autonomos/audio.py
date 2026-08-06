"""WAV validation and whisper silence-hallucination rejection.

The browser normalises every recording to 16 kHz mono 16-bit PCM (KD-15), so the
backend has exactly one input format to validate and no ffmpeg dependency. Audio
is held in memory, forwarded to the loopback sidecar, and never written to disk
(15.1).
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass

from .errors import ApiError
from .parsing.text import normalize

REQUIRED_SAMPLE_RATE = 16_000
REQUIRED_CHANNELS = 1
REQUIRED_BITS = 16
PCM_FORMAT = 1

# R5: Spanish whisper models emit boilerplate on near-silence. Left unhandled it
# becomes a journal entry or a nonsense expense description, so these are
# rejected as `transcription_failed` (8.4) rather than returned as a transcript.
HALLUCINATION_PATTERNS = [
    re.compile(r"subtitulos? (realizados|por|creados)"),
    re.compile(r"amara\.?org"),
    re.compile(r"subtitulado por la comunidad"),
    re.compile(r"gracias por ver el video"),
    re.compile(r"suscribete al canal"),
    re.compile(r"^\W*$"),
]
_BRACKETED_ONLY_RE = re.compile(r"^[\[\(][^\]\)]*[\]\)][\s.]*$")


class AudioInvalid(ApiError):
    def __init__(self, message: str = "audio is not 16 kHz mono 16-bit PCM WAV"):
        super().__init__(415, "audio_invalid", message)


class AudioTooLong(ApiError):
    def __init__(self, message: str = "audio exceeds MAX_AUDIO_S"):
        super().__init__(413, "audio_too_long", message)


@dataclass(frozen=True)
class WavInfo:
    sample_rate: int
    channels: int
    bits_per_sample: int
    frames: int

    @property
    def duration_s(self) -> float:
        return self.frames / self.sample_rate if self.sample_rate else 0.0

    @property
    def duration_ms(self) -> int:
        return int(round(self.duration_s * 1000))


def parse_wav(data: bytes) -> WavInfo:
    if len(data) < 44 or data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise AudioInvalid("not a RIFF/WAVE container")
    offset = 12
    fmt: tuple[int, int, int, int] | None = None
    data_size: int | None = None
    while offset + 8 <= len(data):
        chunk_id = data[offset : offset + 4]
        (chunk_size,) = struct.unpack_from("<I", data, offset + 4)
        body = offset + 8
        if chunk_id == b"fmt " and chunk_size >= 16:
            audio_format, channels, sample_rate, _byte_rate, _align, bits = (
                struct.unpack_from("<HHIIHH", data, body)
            )
            fmt = (audio_format, channels, sample_rate, bits)
        elif chunk_id == b"data":
            data_size = min(chunk_size, len(data) - body)
        offset = body + chunk_size + (chunk_size % 2)
    if fmt is None or data_size is None:
        raise AudioInvalid("missing fmt or data chunk")

    audio_format, channels, sample_rate, bits = fmt
    if audio_format != PCM_FORMAT:
        raise AudioInvalid("not uncompressed PCM")
    if channels != REQUIRED_CHANNELS:
        raise AudioInvalid("audio must be mono")
    if sample_rate != REQUIRED_SAMPLE_RATE:
        raise AudioInvalid("audio must be 16000 Hz")
    if bits != REQUIRED_BITS:
        raise AudioInvalid("audio must be 16-bit")

    frame_bytes = channels * bits // 8
    return WavInfo(sample_rate, channels, bits, data_size // frame_bytes)


def validate_audio(
    data: bytes, *, max_audio_s: float, max_bytes: int, min_audio_s: float
) -> WavInfo:
    if len(data) > max_bytes:
        raise AudioTooLong(f"payload {len(data)} bytes over the {max_bytes} limit")
    info = parse_wav(data)
    if info.duration_s > max_audio_s:
        raise AudioTooLong(f"{info.duration_s:.1f}s over the {max_audio_s}s cap")
    if info.duration_s < min_audio_s:
        # Too short to contain speech: whisper would answer with boilerplate.
        raise ApiError(422, "transcription_failed", "audio too short to contain speech")
    return info


def looks_hallucinated(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return True
    # whisper marks non-speech with a bracketed token — `[Música]`,
    # `[BLANK_AUDIO]`, `(silencio)`. Observed on this host, 2026-08-05, when a
    # tone was sent instead of speech. A whole transcript that is one bracketed
    # token is never something the user said.
    if _BRACKETED_ONLY_RE.match(raw):
        return True
    candidate = normalize(raw)
    if not candidate:
        return True
    return any(pattern.search(candidate) for pattern in HALLUCINATION_PATTERNS)
