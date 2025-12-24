"""tests/test_files_and_batches_integration.py

Integration tests for the relay's Files + Batches behavior.

These tests are intentionally "black box": they talk to a *running* relay instance
over HTTP (local uvicorn on :8000, or a deployed URL).

Environment
-----------
RELAY_BASE_URL
  Base URL for the relay. Defaults to http://localhost:8000

RELAY_TOKEN / RELAY_KEY
  Relay auth token. Tests prefer RELAY_TOKEN, and fall back to RELAY_KEY.

INTEGRATION_OPENAI_API_KEY
  Gate for upstream-hitting tests. If unset/empty, expensive OpenAI-dependent tests
  are skipped (to keep default CI runs cheap/safe).
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, AsyncIterator, Dict

import httpx
import pytest
import pytest_asyncio

RELAY_BASE_URL = (os.getenv("RELAY_BASE_URL") or "http://localhost:8000").rstrip("/")
RELAY_TOKEN = os.getenv("RELAY_TOKEN") or os.getenv("RELAY_KEY") or "dummy"

INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


DEFAULT_TIMEOUT_S = _env_float("RELAY_TEST_TIMEOUT_S", 60.0)


def _has_openai_key() -> bool:
    return bool(os.getenv(INTEGRATION_ENV_VAR))


def _auth_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    """
    Send both headers so tests work across relay deployments that check either:
      - Authorization: Bearer <token>
      - X-Relay-Key: <token>
    """
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {RELAY_TOKEN}",
        "X-Relay-Key": RELAY_TOKEN,
    }
    if extra:
        headers.update(extra)
    return headers


async def _request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    retries: int = 2,
    retry_sleep_s: float = 0.5,
    **kwargs: Any,
) -> httpx.Response:
    last_exc: Exception | None = None
    last_resp: httpx.Response | None = None

    for attempt in range(retries + 1):
        try:
            resp = await client.request(method, url, **kwargs)
            last_resp = resp
            # For tests: return any non-5xx response so assertions can inspect it.
            if resp.status_code < 500:
                return resp
        except httpx.HTTPError as exc:
            last_exc = exc

        if attempt < retries:
            await asyncio.sleep(retry_sleep_s)

    if last_resp is not None:
        return last_resp
    assert last_exc is not None
    raise last_exc


@pytest_asyncio.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """
    IMPORTANT FIX:
    In `asyncio_mode=strict`, async fixtures must use `@pytest_asyncio.fixture`.
    Otherwise pytest passes an async generator object through to tests and you get:
      AttributeError: 'async_generator' object has no attribute 'request'
    """
    async with httpx.AsyncClient(
        base_url=RELAY_BASE_URL,
        timeout=DEFAULT_TIMEOUT_S,
        headers=_auth_headers(),
    ) as c:
        yield c


@pytest.mark.integration
@pytest.mark.asyncio
async def test_proxy_blocks_evals_and_fine_tune(client: httpx.AsyncClient) -> None:
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    # Evals blocked
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={"method": "GET", "path": "/v1/evals"},
    )
    assert r.status_code in (403, 404), f"Unexpected evals proxy status: {r.status_code} {r.text[:200]}"

    # Fine-tune blocked
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={"method": "GET", "path": "/v1/fine_tuning/jobs"},
    )
    assert r.status_code in (403, 404), f"Unexpected fine-tune proxy status: {r.status_code} {r.text[:200]}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_data_file_download_is_forbidden(client: httpx.AsyncClient) -> None:
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    data = {"purpose": "user_data"}
    files = {"file": ("relay_ping.txt", b"ping", "text/plain")}

    r = await _request_with_retry(
        client,
        "POST",
        "/v1/files",
        headers=_auth_headers(),
        data=data,
        files=files,
    )
    assert r.status_code < 500, f"file upload returned {r.status_code}: {r.text[:400]}"
    body = r.json()
    file_id = body.get("id")
    assert isinstance(file_id, str) and file_id, f"unexpected file id: {body}"

    # user_data file downloads should be forbidden by relay (privacy guardrail)
    r = await _request_with_retry(client, "GET", f"/v1/files/{file_id}/content", headers=_auth_headers())
    assert r.status_code in (401, 403), f"expected forbidden, got {r.status_code}: {r.text[:200]}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_batch_output_file_is_downloadable(client: httpx.AsyncClient) -> None:
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
    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_headers(), data=data, files=files)
    assert r.status_code < 500, f"batch input upload returned {r.status_code}: {r.text[:400]}"
    file_id = r.json().get("id")
    assert isinstance(file_id, str) and file_id, f"unexpected batch input file id: {r.text[:200]}"

    # Create batch
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/batches",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={
            "input_file_id": file_id,
            "endpoint": "/v1/responses",
            "completion_window": "24h",
        },
    )
    assert r.status_code < 500, f"batch create returned {r.status_code}: {r.text[:400]}"
    batch = r.json()
    batch_id = batch.get("id")
    assert isinstance(batch_id, str) and batch_id, f"unexpected batch id: {batch}"

    # Poll status
    loop = asyncio.get_running_loop()
    deadline = loop.time() + batch_timeout_s

    output_file_id: str | None = None
    status: str | None = None

    while loop.time() < deadline:
        r = await _request_with_retry(client, "GET", f"/v1/batches/{batch_id}", headers=_auth_headers())
        assert r.status_code < 500, f"batch retrieve returned {r.status_code}: {r.text[:200]}"

        body = r.json()
        status = body.get("status")
        output_file_id = body.get("output_file_id")

        if status == "completed" and isinstance(output_file_id, str) and output_file_id:
            break

        if status in ("failed", "expired", "cancelled"):
            pytest.fail(f"batch ended unexpectedly with status={status}: {body}")

        await asyncio.sleep(poll_interval_s)

    if status != "completed" or not output_file_id:
        pytest.skip(f"batch did not complete within {batch_timeout_s}s (last status={status})")

    # Download output file content
    r = await _request_with_retry(client, "GET", f"/v1/files/{output_file_id}/content", headers=_auth_headers())
    assert r.status_code < 500, f"output file content returned {r.status_code}: {r.text[:200]}"
    assert r.status_code == 200, f"expected 200 for output file, got {r.status_code}: {r.text[:200]}"
    assert r.content, "output file content was empty"
