from __future__ import annotations

import contextlib
import json
import os
import time
from typing import Any, Dict, Optional

import httpx
import pytest

INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"


def _base_url() -> str:
    # Prefer an explicit RELAY_BASE_URL so we can run this suite against Render.
    # Falls back to local dev server if unset.
    raw = os.environ.get("RELAY_BASE_URL", "http://localhost:8000")
    return raw.rstrip("/")


BASE_URL = _base_url()


def _relay_key() -> str:
    # Accept multiple env var spellings to reduce configuration footguns.
    return (
        os.environ.get("RELAY_TOKEN")
        or os.environ.get("RELAY_KEY")
        or os.environ.get("RELAY_AUTH_TOKEN")
        or "dummy"
    )


def _auth_header() -> Dict[str, str]:
    return {"Authorization": f"Bearer {_relay_key()}"}


def _has_openai_key() -> bool:
    # Intentional "are you sure" toggle; does NOT contain the real upstream key.
    return bool(os.getenv(INTEGRATION_ENV_VAR))


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@pytest.fixture
async def client() -> httpx.AsyncClient:
    """
    These tests run against a *running relay* (local or remote).
    If the relay isn't reachable, skip with a clear message instead of raising ConnectError.
    """
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180.0) as c:
        try:
            ping = await c.get("/v1/actions/ping")
        except httpx.HTTPError as e:
            pytest.skip(
                f"Relay not reachable at BASE_URL={BASE_URL!r}. "
                f"Start uvicorn locally or set RELAY_BASE_URL to your deployed relay. "
                f"Underlying error: {e!r}"
            )
        if ping.status_code != 200:
            pytest.skip(
                f"Relay ping at {BASE_URL!r} returned HTTP {ping.status_code}. "
                f"Body: {(ping.text or '')[:300]}"
            )
        yield c


async def _request_with_retry(
    client: httpx.AsyncClient, method: str, url: str, *, retries: int = 2, backoff_s: float = 0.5, **kwargs: Any
) -> httpx.Response:
    """
    Simple retries for transient network issues (Render cold starts, etc.).
    """
    last_exc: Optional[Exception] = None
    for i in range(retries + 1):
        try:
            r = await client.request(method, url, **kwargs)
            return r
        except httpx.HTTPError as e:
            last_exc = e
            if i < retries:
                time.sleep(backoff_s * (i + 1))
                continue
            raise
    assert last_exc is not None
    raise last_exc


@pytest.mark.integration
@pytest.mark.asyncio
async def test_proxy_blocks_evals_and_fine_tune(client: httpx.AsyncClient):
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    # Evals blocked
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"method": "GET", "path": "/v1/evals"},
    )
    assert r.status_code in (403, 404), f"Expected 403/404 for evals; got {r.status_code}: {r.text[:400]}"

    # Fine-tunes blocked
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"method": "GET", "path": "/v1/fine_tuning/jobs"},
    )
    assert r.status_code in (403, 404), f"Expected 403/404 for fine_tuning; got {r.status_code}: {r.text[:400]}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_data_file_download_is_forbidden(client: httpx.AsyncClient):
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    data = {"purpose": "user_data"}
    files = {"file": ("relay_ping.txt", b"ping", "text/plain")}

    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)
    assert r.status_code == 200, f"File upload failed: {r.status_code} {r.text[:400]}"
    file_id = r.json().get("id")
    assert isinstance(file_id, str) and file_id.startswith("file-")

    # Attempt download - should be blocked by relay policy for user_data.
    r = await _request_with_retry(client, "GET", f"/v1/files/{file_id}/content", headers=_auth_header())
    assert r.status_code in (403, 404), f"Expected 403/404 download block; got {r.status_code}: {r.text[:400]}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_batch_output_file_is_downloadable(client: httpx.AsyncClient):
    """
    Batch completion latency is not deterministic. The relay is correct if:
      - batch can be created
      - status progresses (validating/in_progress/finalizing)
      - once completed, output_file_id content downloads successfully

    If the batch does not complete within the configured timeout, skip rather than fail.
    """
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    batch_timeout_s = _env_float("BATCH_TIMEOUT_SECONDS", 600.0)
    poll_interval_s = _env_float("BATCH_POLL_INTERVAL_SECONDS", 2.0)

    jsonl_line = (
        json.dumps(
            {
                "custom_id": "ping-1",
                "method": "POST",
                "url": "/v1/responses",
                "body": {"model": "gpt-5.1", "input": "Return exactly: pong"},
            }
        ).encode("utf-8")
        + b"\n"
    )

    # Upload batch input
    data = {"purpose": "batch"}
    files = {"file": ("batch_input.jsonl", jsonl_line, "application/jsonl")}
    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)
    assert r.status_code == 200, f"Batch input upload failed: {r.status_code} {r.text[:400]}"
    input_file_id = r.json().get("id")
    assert isinstance(input_file_id, str) and input_file_id.startswith("file-")

    # Create batch
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/batches",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"input_file_id": input_file_id, "endpoint": "/v1/responses", "completion_window": "24h"},
    )
    assert r.status_code == 200, f"Batch create failed: {r.status_code} {r.text[:400]}"
    batch_id = r.json().get("id")
    assert isinstance(batch_id, str) and batch_id.startswith("batch_")

    # Poll for completion
    deadline = time.time() + batch_timeout_s
    status = None
    output_file_id = None

    while time.time() < deadline:
        r = await _request_with_retry(client, "GET", f"/v1/batches/{batch_id}", headers=_auth_header())
        assert r.status_code == 200, f"Batch get failed: {r.status_code} {r.text[:400]}"
        body = r.json()
        status = body.get("status")
        output_file_id = body.get("output_file_id")

        if status == "completed" and isinstance(output_file_id, str) and output_file_id.startswith("file-"):
            break

        if status in ("failed", "expired", "cancelled"):
            pytest.fail(f"Batch ended unexpectedly: status={status} body={str(body)[:800]}")

        time.sleep(poll_interval_s)

    if status != "completed" or not isinstance(output_file_id, str):
        pytest.skip(f"Batch did not complete within {batch_timeout_s}s (last status={status}).")

    # Download output
    r = await _request_with_retry(client, "GET", f"/v1/files/{output_file_id}/content", headers=_auth_header())
    assert r.status_code == 200, f"Output file download failed: {r.status_code} {r.text[:400]}"
    assert len(r.content) > 0, "Output file content was empty"
