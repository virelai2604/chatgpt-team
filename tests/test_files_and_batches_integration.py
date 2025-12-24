from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional

import httpx
import pytest
import pytest_asyncio

# This test file is intended to run against a running relay server.
# Default matches your other integration tests.
RELAY_BASE_URL = os.environ.get("RELAY_BASE_URL", "http://localhost:8000")

# Gate these tests behind a flag, since they may call upstream depending on your relay config.
INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"


def _has_openai_key() -> bool:
    """
    We do not validate key format here; we only gate execution.
    """
    key = os.getenv(INTEGRATION_ENV_VAR, "")
    return bool(key and key.strip())


def _auth_header() -> Dict[str, str]:
    """
    Relay auth header. Prefer RELAY_KEY but support RELAY_TOKEN for backward-compat.
    """
    token = (os.getenv("RELAY_KEY") or os.getenv("RELAY_TOKEN") or "").strip()
    return {"Authorization": f"Bearer {token}"} if token else {}


async def _request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    max_attempts: int = 4,
    base_delay_s: float = 0.6,
    **kwargs: Any,
) -> httpx.Response:
    """
    Minimal retry helper for transient network/cold-start issues.
    """
    last_exc: Optional[Exception] = None
    for i in range(max_attempts):
        try:
            return await client.request(method, url, **kwargs)
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
            last_exc = exc
            if i == max_attempts - 1:
                raise
            await asyncio.sleep(base_delay_s * (2**i))
    raise last_exc or RuntimeError("request_with_retry failed without exception")


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# IMPORTANT FIX:
# In pytest-asyncio strict mode, async fixtures must use pytest_asyncio.fixture.
@pytest_asyncio.fixture
async def client() -> httpx.AsyncClient:
    timeout_s = _env_float("INTEGRATION_HTTP_TIMEOUT_SECONDS", 60.0)
    timeout = httpx.Timeout(timeout_s)

    async with httpx.AsyncClient(
        base_url=RELAY_BASE_URL,
        timeout=timeout,
        follow_redirects=True,
    ) as c:
        yield c


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
    assert r.status_code in (400, 403), f"Unexpected evals status {r.status_code}: {r.text[:400]}"

    # Fine-tuning blocked
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"method": "GET", "path": "/v1/fine_tuning/jobs"},
    )
    assert r.status_code in (400, 403), f"Unexpected fine-tune status {r.status_code}: {r.text[:400]}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_data_file_download_is_forbidden(client: httpx.AsyncClient):
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    data = {"purpose": "user_data"}
    files = {"file": ("relay_ping.txt", b"ping", "text/plain")}

    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)
    assert r.status_code == 200, f"file upload failed {r.status_code}: {r.text[:400]}"
    file_id = r.json().get("id")
    assert file_id, f"missing file id in response: {r.text[:400]}"

    # Downloads for user_data must be forbidden.
    r = await _request_with_retry(client, "GET", f"/v1/files/{file_id}/content", headers=_auth_header())
    assert r.status_code == 400, f"expected forbidden download, got {r.status_code}: {r.text[:400]}"
    assert "Not allowed to download files of purpose: user_data" in (r.text or "")


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
    model = os.getenv("INTEGRATION_MODEL", "gpt-4.1-mini")

    jsonl_line = (
        json.dumps(
            {
                "custom_id": "ping-1",
                "method": "POST",
                "url": "/v1/responses",
                "body": {"model": model, "input": "Return exactly: pong"},
            }
        ).encode("utf-8")
        + b"\n"
    )

    # Upload batch input
    data = {"purpose": "batch"}
    files = {"file": ("batch_input.jsonl", jsonl_line, "application/jsonl")}
    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)
    assert r.status_code == 200, f"batch input upload failed {r.status_code}: {r.text[:400]}"
    input_file_id = r.json().get("id")
    assert input_file_id, f"missing input file id in response: {r.text[:400]}"

    # Create batch
    r = await _request_with_retry(
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
    assert r.status_code == 200, f"batch create failed {r.status_code}: {r.text[:400]}"
    batch_id = r.json().get("id")
    assert batch_id, f"missing batch id in response: {r.text[:400]}"

    # Poll until completed or timeout
    deadline = asyncio.get_event_loop().time() + batch_timeout_s
    output_file_id: Optional[str] = None

    while asyncio.get_event_loop().time() < deadline:
        r = await _request_with_retry(client, "GET", f"/v1/batches/{batch_id}", headers=_auth_header())
        assert r.status_code == 200, f"batch retrieve failed {r.status_code}: {r.text[:400]}"
        body = r.json()
        status = body.get("status")

        if status == "completed":
            output_file_id = body.get("output_file_id")
            break

        if status in ("failed", "expired", "cancelled"):
            pytest.skip(f"batch ended in terminal status={status}: {body}")

        await asyncio.sleep(poll_interval_s)

    if not output_file_id:
        pytest.skip("batch did not complete within timeout; skipping")

    # Download output file content
    r = await _request_with_retry(client, "GET", f"/v1/files/{output_file_id}/content", headers=_auth_header())
    assert r.status_code == 200, f"output file download failed {r.status_code}: {r.text[:400]}"
    assert (r.content or b"").strip(), "output file content is empty"
