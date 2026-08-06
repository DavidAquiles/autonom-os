"""`POST /api/voice/transcribe` (Requirements 8, 9, 10) and audio validation."""

from __future__ import annotations

import time

import pytest

from autonomos.audio import looks_hallucinated, parse_wav, validate_audio
from autonomos.errors import ApiError
from autonomos.providers.base import ProviderTimeout, ProviderUnavailable
from tests.conftest import wav_bytes


def post_audio(client, data=None, context="expense"):
    return client.post(
        "/api/voice/transcribe",
        files={"audio": ("clip.wav", data if data is not None else wav_bytes(2.0), "audio/wav")},
        data={"context": context},
    )


def test_8_2_and_9_1_expense_context_returns_transcript_and_draft(client, fake_stt):
    fake_stt.transcript = "gasté catorce mil pesos en uber con la tarjeta de crédito"
    body = post_audio(client).json()
    assert body["transcript"] == fake_stt.transcript
    assert body["audio_ms"] == 2000
    assert body["elapsed_ms"] >= 0
    draft = body["draft"]
    assert draft["amount_cop"] == 14000
    assert draft["category_name"] == "Transporte"
    assert draft["payment_method_name"] == "Tarjeta de crédito"
    assert draft["description_truncated"] is False


def test_9_2_undetermined_fields_are_none_with_resolved_by_none(client, fake_stt):
    fake_stt.transcript = "compré algo indescriptible"
    draft = post_audio(client).json()["draft"]
    assert draft["amount_cop"] is None
    assert draft["payment_method_id"] is None
    assert draft["resolved_by"]["amount"] == "none"
    assert draft["resolved_by"]["payment_method"] == "none"


def test_10_1_and_10_2_journal_context_returns_the_words_verbatim(client, fake_stt):
    fake_stt.transcript = "Hoy me sentí raro, como si nada encajara. Mañana veré."
    body = post_audio(client, context="journal").json()
    assert body["transcript"] == fake_stt.transcript
    assert body["draft"] is None  # no post-processing path exists at all (KD-9)


def test_question_context_returns_no_draft(client, fake_stt):
    fake_stt.transcript = "¿cuánto gasté este mes?"
    assert post_audio(client, context="question").json()["draft"] is None


def test_8_3_transcribing_writes_nothing_to_the_database(client, fake_stt):
    post_audio(client)
    post_audio(client, context="journal")
    assert client.get("/api/expenses").json()["total_count"] == 0
    assert client.get("/api/journal").json()["items"] == []


def test_invalid_context_is_a_validation_error(client):
    response = post_audio(client, context="gimnasio")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation"


def test_non_wav_payload_is_audio_invalid(client):
    response = post_audio(client, data=b"this is not a wav file at all")
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "audio_invalid"


def test_wrong_sample_rate_is_audio_invalid(client):
    response = post_audio(client, data=wav_bytes(1.0, sample_rate=44100))
    assert response.status_code == 415


def test_stereo_is_audio_invalid(client):
    response = post_audio(client, data=wav_bytes(1.0, channels=2))
    assert response.status_code == 415


def test_audio_over_the_cap_is_rejected(client):
    response = post_audio(client, data=wav_bytes(33.0))
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "audio_too_long"


def test_32_seconds_is_accepted(client, fake_stt):
    """KD-5: the cap deliberately crosses into a second whisper window."""
    assert post_audio(client, data=wav_bytes(32.0)).status_code == 200


def test_8_4_silence_is_transcription_failed_not_an_empty_record(client, fake_stt):
    fake_stt.transcript = ""
    response = post_audio(client)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "transcription_failed"


def test_r5_known_silence_hallucination_is_rejected(client, fake_stt):
    fake_stt.transcript = "Subtítulos realizados por la comunidad de Amara.org"
    response = post_audio(client)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "transcription_failed"


def test_8_4_sidecar_timeout_is_reported_as_such(client, fake_stt):
    fake_stt.raise_error = ProviderTimeout("too slow")
    response = post_audio(client)
    assert response.status_code == 504
    assert response.json()["error"]["code"] == "transcription_timeout"


def test_sidecar_down_is_transcription_failed_never_llm_unavailable(client, fake_stt):
    fake_stt.raise_error = ProviderUnavailable("connection refused")
    response = post_audio(client)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "transcription_failed"


def test_11_17_and_kd12_transcription_preempts_a_running_question(client, sidecars):
    """A voice capture takes priority; the question ends as `preempted`, which is
    a legitimate 11.12 outcome rather than a silent loss."""
    fake_llm, fake_stt = sidecars
    client.post(
        "/api/expenses",
        json={"amount_cop": 14000, "category_id": 1, "payment_method_id": 1},
    )
    fake_llm.delay_s = 5.0
    job = client.post(
        "/api/insights/questions", json={"question": "¿cuánto gasté hoy?"}
    ).json()
    time.sleep(0.2)  # let generation actually start

    assert post_audio(client).status_code == 200

    deadline = time.time() + 3.0
    body = client.get(f"/api/insights/questions/{job['job_id']}").json()
    while body["status"] in ("queued", "running") and time.time() < deadline:
        time.sleep(0.05)
        body = client.get(f"/api/insights/questions/{job['job_id']}").json()
    assert body["status"] == "failed"
    assert body["error_code"] == "preempted"


# --- unit level -----------------------------------------------------------


def test_wav_header_parsing():
    info = parse_wav(wav_bytes(1.5))
    assert info.sample_rate == 16000
    assert info.channels == 1
    assert info.bits_per_sample == 16
    assert info.duration_ms == 1500


def test_validate_rejects_a_clip_too_short_to_hold_speech():
    with pytest.raises(ApiError) as excinfo:
        validate_audio(
            wav_bytes(0.1), max_audio_s=32, max_bytes=2_000_000, min_audio_s=0.4
        )
    assert excinfo.value.code == "transcription_failed"


def test_validate_rejects_an_oversized_payload():
    with pytest.raises(ApiError) as excinfo:
        validate_audio(wav_bytes(2.0), max_audio_s=32, max_bytes=1000, min_audio_s=0.4)
    assert excinfo.value.code == "audio_too_long"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Subtítulos realizados por la comunidad de Amara.org", True),
        ("   ", True),
        # Observed live on this host when a tone was sent instead of speech.
        ("[Música]", True),
        ("[BLANK_AUDIO]", True),
        ("(silencio)", True),
        ("gasté catorce mil pesos", False),
        ("Fui al concierto y la música estuvo buenísima", False),
    ],
)
def test_hallucination_patterns(text, expected):
    assert looks_hallucinated(text) is expected
