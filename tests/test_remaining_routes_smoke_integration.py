import os
import requests
import pytest

RELAY_BASE_URL = (os.getenv("RELAY_BASE_URL") or "http://localhost:8000").rstrip("/")
RELAY_TOKEN = os.getenv("RELAY_TOKEN") or os.getenv("RELAY_KEY") or "dummy"

DEFAULT_TIMEOUT_S = float(os.getenv("RELAY_TEST_TIMEOUT_S", "30"))


def _auth_headers(extra: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {RELAY_TOKEN}",
        "X-Relay-Key": RELAY_TOKEN,
    }
    if extra:
        headers.update(extra)
    return headers


@pytest.mark.integration
def test_files_list_no_5xx():
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/files?limit=1",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"/v1/files returned {r.status_code}: {r.text[:200]}"


@pytest.mark.integration
def test_files_retrieve_missing_is_404_or_4xx():
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/files/file_DOES_NOT_EXIST",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500


@pytest.mark.integration
def test_batches_list_no_5xx():
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/batches?limit=1",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"/v1/batches returned {r.status_code}: {r.text[:200]}"


@pytest.mark.integration
def test_moderations_wiring_no_5xx():
    # We don't assert on policy outputs; this is just wiring/no-5xx.
    payload = {"model": "omni-moderation-latest", "input": "Hello world"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/moderations",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"/v1/moderations returned {r.status_code}: {r.text[:200]}"


@pytest.mark.integration
def test_audio_speech_wiring_no_5xx():
    # The relay might not support audio on all deployments; accept 4xx as "no 5xx wiring".
    payload = {"model": "gpt-4o-mini-tts", "input": "hello", "voice": "alloy"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/audio/speech",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"/v1/audio/speech returned {r.status_code}: {r.text[:200]}"


@pytest.mark.integration
def test_transcriptions_wiring_no_5xx():
    # Requires multipart form data; accept 4xx as ok, fail only on 5xx.
    files = {"file": ("sample.wav", b"RIFFxxxxWAVEfmt ", "audio/wav")}
    data = {"model": "gpt-4o-mini-transcribe"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/audio/transcriptions",
        headers=_auth_headers(),
        files=files,
        data=data,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"/v1/audio/transcriptions returned {r.status_code}: {r.text[:200]}"


@pytest.mark.integration
def test_embeddings_wiring_no_5xx():
    payload = {"model": "text-embedding-3-small", "input": "hello"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/embeddings",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"/v1/embeddings returned {r.status_code}: {r.text[:200]}"


@pytest.mark.integration
def test_fine_tuning_list_blocked_or_no_5xx():
    # If your relay blocks fine-tuning, you should see 403/404. Otherwise expect no 5xx.
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/fine_tuning/jobs?limit=1",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"/v1/fine_tuning/jobs returned {r.status_code}: {r.text[:200]}"


@pytest.mark.integration
def test_evals_list_blocked_or_no_5xx():
    # Evals may be blocked by policy; accept 403/404; fail only on 5xx.
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/evals?limit=1",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"/v1/evals returned {r.status_code}: {r.text[:200]}"
