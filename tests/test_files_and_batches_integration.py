import asyncio
import json
import os
import time
from typing import Any, Dict, Optional

import httpx
import pytest
import pytest_asyncio

INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"


def _has_openai_key() -> bool:
    # This flag controls whether integration tests run.
    return bool(os.getenv(INTEGRATION_ENV_VAR))


def _auth_header() -> Dict[str, str]:
    # Relay auth header (your relay checks this; upstream OpenAI key is server-side)
    return {"Authorization": f"Bearer {os.getenv('RELAY_KEY', 'dummy')}"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


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
    Integration runs can see transient upstream 502/503/504.
    Retry a few times; if still failing, return the last response.
    """
    for attempt in range(1, max_attempts + 1):
        r = await client.request(method, url, **kwargs)
        if r.status_code in (502, 503, 504):
            if attempt == max_attempts:
                return r
            await asyncio.sleep(base_delay_s * (2 ** (attempt - 1)))
            continue
        return r
    return r  # pragma: no cover


@pytest_asyncio.fixture
async def client() -> httpx.AsyncClient:
    # Keep timeout high enough for multipart uploads and batch polling.
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=180.0) as c:
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
    assert r.status_code in (400, 403), r.text

    # Fine-tuning blocked
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"method": "GET", "path": "/v1/fine_tuning/jobs"},
    )
    assert r.status_code in (400, 403), r.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_data_file_download_is_forbidden(client: httpx.AsyncClient):
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    data = {"purpose": "user_data"}
    files = {"file": ("relay_ping.txt", b"ping", "text/plain")}

    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)
    if r.status_code in (502, 503, 504):
        pytest.skip(f"Upstream unavailable (status={r.status_code}): {r.text}")
    assert r.status_code == 200, r.text

    file_id = r.json()["id"]

    # Download must be forbidden for purpose=user_data (OpenAI policy behavior)
    r = await _request_with_retry(client, "GET", f"/v1/files/{file_id}/content", headers=_auth_header())
    assert r.status_code == 400, r.text
    body = r.json()
    assert "Not allowed to download files of purpose: user_data" in body["error"]["message"]


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
    if r.status_code in (502, 503, 504):
        pytest.skip(f"Upstream unavailable (status={r.status_code}): {r.text}")
    assert r.status_code == 200, r.text
    input_file_id = r.json()["id"]

    # Create batch
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/batches",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"input_file_id": input_file_id, "endpoint": "/v1/responses", "completion_window": "24h"},
    )
    if r.status_code in (502, 503, 504):
        pytest.skip(f"Upstream unavailable (status={r.status_code}): {r.text}")
    assert r.status_code == 200, r.text
    batch_id = r.json()["id"]

    # Poll batch until completed
    output_file_id: Optional[str] = None
    last_status: Optional[str] = None
    last_payload: Optional[dict[str, Any]] = None

    deadline = time.time() + batch_timeout_s

    # Optional gentle backoff to reduce load if it runs long.
    interval = max(0.5, poll_interval_s)

    while time.time() < deadline:
        r = await _request_with_retry(client, "GET", f"/v1/batches/{batch_id}", headers=_auth_header())
        if r.status_code in (502, 503, 504):
            await asyncio.sleep(interval)
            continue

        assert r.status_code == 200, r.text
        j = r.json()
        last_payload = j
        last_status = j.get("status")

        if last_status == "completed":
            output_file_id = j.get("output_file_id")
            break

        if last_status in ("failed", "expired", "cancelled"):
            pytest.fail(f"Batch ended in terminal status={last_status}: {j}")

        # Backoff after a bit to avoid hammering.
        await asyncio.sleep(interval)
        if interval < 5.0:
            interval = min(5.0, interval + 0.2)

    if not output_file_id:
        pytest.skip(
            f"Batch did not complete within {batch_timeout_s:.0f}s (status={last_status}). "
            f"Set BATCH_TIMEOUT_SECONDS higher if needed. Last payload={last_payload}"
        )

    # Download output file content: should be JSONL including "pong"
    r = await _request_with_retry(client, "GET", f"/v1/files/{output_file_id}/content", headers=_auth_header())
    assert r.status_code == 200, r.text
    assert "pong" in r.text
