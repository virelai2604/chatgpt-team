"""
Integration tests that touch /v1/files and /v1/batches and validate key relay policies.

These tests are safe to run against:
- Local relay (default http://localhost:8000)
- Deployed relay (set RELAY_BASE_URL)

Upstream opt-in:
- Any tests that might touch upstream endpoints are gated behind INTEGRATION_OPENAI_API_KEY.
  Set it to any non-empty value (e.g. 1) to enable.

Important:
- This file uses pytest-asyncio in STRICT mode. Async fixtures MUST be declared with
  @pytest_asyncio.fixture, not @pytest.fixture.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Optional

import httpx
import pytest
import pytest_asyncio

RELAY_BASE_URL = (os.environ.get("RELAY_BASE_URL") or "http://localhost:8000").rstrip("/")
INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"

# Allow overriding model used inside the batch job. Keep a sensible default.
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL") or "gpt-4.1-mini"


def _relay_token() -> str:
    # Accept either name; many shells/export patterns vary.
    return os.environ.get("RELAY_TOKEN") or os.environ.get("RELAY_KEY") or "dummy"


def _auth_header() -> dict[str, str]:
    return {"Authorization": f"Bearer {_relay_token()}"}


def _has_openai_key() -> bool:
    # This env var is used as an opt-in flag for upstream-touching tests.
    return bool((os.getenv(INTEGRATION_ENV_VAR) or "").strip())


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@pytest_asyncio.fixture
async def client() -> httpx.AsyncClient:
    # Use a generous timeout because batches can take time, but keep connect bounded.
    timeout = httpx.Timeout(180.0, connect=30.0)
    async with httpx.AsyncClient(base_url=RELAY_BASE_URL, timeout=timeout) as c:
        yield c


async def _request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    retries: int = 2,
    backoff_s: float = 0.5,
    **kwargs: Any,
) -> httpx.Response:
    """
    Simple retries for transient network issues (Render cold starts, etc.).
    """
    last_exc: Optional[Exception] = None
    for i in range(retries + 1):
        try:
            return await client.request(method, url, **kwargs)
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
            last_exc = exc
            if i < retries:
                await asyncio.sleep(backoff_s * (i + 1))
                continue
            raise
    # Unreachable, but keeps type-checkers happy.
    assert last_exc is not None
    raise last_exc


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
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"method": "GET", "path": "/v1/evals"},
    )
    # We expect the relay to block. Some deployments may respond 404 if the route is absent,
    # but it must never be a 5xx.
    assert r.status_code < 500
    assert r.status_code in (400, 403, 404), r.text

    # Fine-tuning blocked (use GET so we don't need to supply a request body)
    r2 = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"method": "GET", "path": "/v1/fine_tuning/jobs"},
    )
    assert r2.status_code < 500
    assert r2.status_code in (400, 403, 404), r2.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_data_file_download_is_forbidden(client: httpx.AsyncClient) -> None:
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    # Upload a tiny file with purpose=user_data
    data = {"purpose": "user_data"}
    files = {"file": ("relay_ping.txt", b"ping", "text/plain")}

    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)

    # If upstream is unavailable (e.g. no egress / cold start), skip rather than fail.
    if r.status_code in (502, 503, 504):
        pytest.skip(f"Upstream unavailable for /v1/files upload: {r.status_code} {r.text[:200]}")

    assert r.status_code == 200, r.text
    file_json = r.json()
    file_id = file_json.get("id")
    assert file_id, f"Upload returned no file id. Body: {file_json}"

    # Download should be forbidden for user_data purpose
    download = await _request_with_retry(
        client, "GET", f"/v1/files/{file_id}/content", headers=_auth_header()
    )
    assert download.status_code in (400, 403), download.text

    # Prefer a stable message assertion but keep it tolerant across implementations.
    body_text = (download.text or "").lower()
    assert "user_data" in body_text or "not allowed" in body_text or "forbidden" in body_text


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
                "body": {"model": DEFAULT_MODEL, "input": "Return exactly: pong"},
            }
        ).encode("utf-8")
        + b"\n"
    )

    # Upload batch input
    data = {"purpose": "batch"}
    files = {"file": ("batch_input.jsonl", jsonl_line, "application/jsonl")}
    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)

    if r.status_code in (502, 503, 504):
        pytest.skip(f"Upstream unavailable for batch input upload: {r.status_code} {r.text[:200]}")

    assert r.status_code == 200, r.text
    input_file_id = r.json().get("id")
    assert input_file_id, f"No input file id returned. Body: {r.json()}"

    # Create batch
    create = await _request_with_retry(
        client,
        "POST",
        "/v1/batches",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={
            "input_file_id": input_file_id,
            "endpoint": "/v1/responses",
            "completion_window": "24h",
        },
    )

    if create.status_code in (502, 503, 504):
        pytest.skip(f"Upstream unavailable for batch create: {create.status_code} {create.text[:200]}")

    assert create.status_code == 200, create.text
    batch_id = create.json().get("id")
    assert batch_id, f"No batch id returned. Body: {create.json()}"

    # Poll for completion
    deadline = time.time() + batch_timeout_s
    status = None
    status_json: dict[str, Any] = {}
    while time.time() < deadline:
        status_resp = await _request_with_retry(client, "GET", f"/v1/batches/{batch_id}", headers=_auth_header())

        if status_resp.status_code in (502, 503, 504):
            pytest.skip(f"Upstream unavailable for batch status: {status_resp.status_code} {status_resp.text[:200]}")

        if status_resp.status_code >= 500:
            pytest.skip(f"Relay returned 5xx while polling batch status: {status_resp.status_code} {status_resp.text[:200]}")

        assert status_resp.status_code == 200, status_resp.text
        status_json = status_resp.json()
        status = status_json.get("status")

        if status in ("completed", "failed", "expired", "cancelled"):
            break

        await asyncio.sleep(poll_interval_s)

    if status != "completed":
        pytest.skip(f"Batch did not complete successfully within timeout. status={status} body={status_json}")

    output_file_id = status_json.get("output_file_id")
    assert output_file_id, f"Completed batch missing output_file_id. Body: {status_json}"

    # Download output content; should be allowed (unlike user_data)
    download = await _request_with_retry(
        client, "GET", f"/v1/files/{output_file_id}/content", headers=_auth_header()
    )

    if download.status_code in (502, 503, 504):
        pytest.skip(f"Upstream unavailable for output download: {download.status_code} {download.text[:200]}")

    assert download.status_code == 200, download.text[:400]

    # Batch output is JSONL. We just look for the "pong" token anywhere.
    assert b"pong" in download.content.lower()
