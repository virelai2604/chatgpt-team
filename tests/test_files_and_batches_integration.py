import asyncio
import json
import os
import time
from typing import Any, Dict, Optional

import httpx
import pytest


INTEGRATION_ENV_VAR = "OPENAI_API_KEY"
RELAY_AUTH_HEADER = {"Authorization": "Bearer dummy"}


def _has_openai_key() -> bool:
    return bool(os.getenv(INTEGRATION_ENV_VAR, "").strip())


async def _poll_batch_until_terminal(
    client: httpx.AsyncClient,
    batch_id: str,
    timeout_seconds: int = 240,
    poll_interval_seconds: float = 2.0,
) -> Dict[str, Any]:
    """
    Poll /v1/batches/{batch_id} until the batch reaches a terminal state.
    Returns the final batch object.
    """
    terminal = {"completed", "failed", "expired", "cancelled"}
    deadline = time.time() + timeout_seconds

    last: Optional[Dict[str, Any]] = None
    while time.time() < deadline:
        r = await client.get(f"/v1/batches/{batch_id}", headers=RELAY_AUTH_HEADER)
        r.raise_for_status()
        last = r.json()
        status = last.get("status")
        if status in terminal:
            return last
        await asyncio.sleep(poll_interval_seconds)

    raise AssertionError(f"Batch did not reach terminal state within {timeout_seconds}s; last={last}")


@pytest.fixture
def asgi_app():
    """
    Import the FastAPI app lazily so tests fail fast if the import path breaks.
    """
    from app.main import app  # type: ignore
    return app


@pytest.fixture
async def client(asgi_app):
    """
    In-process client to the relay (no uvicorn required).
    """
    transport = httpx.ASGITransport(app=asgi_app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        timeout=httpx.Timeout(120.0),
        follow_redirects=True,
    ) as c:
        yield c


@pytest.mark.integration
@pytest.mark.asyncio
async def test_proxy_blocks_evals_and_fine_tune(client: httpx.AsyncClient):
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    # Evals blocked
    r = await client.post(
        "/v1/proxy",
        headers={**RELAY_AUTH_HEADER, "Content-Type": "application/json"},
        json={"method": "GET", "path": "/v1/evals"},
    )
    assert r.status_code == 403
    body = r.json()
    assert body.get("error", {}).get("message", "").lower().find("not allowlisted") >= 0

    # Fine-tuning blocked
    r = await client.post(
        "/v1/proxy",
        headers={**RELAY_AUTH_HEADER, "Content-Type": "application/json"},
        json={"method": "POST", "path": "/v1/fine_tuning/jobs", "body": {}},
    )
    assert r.status_code == 403
    body = r.json()
    assert body.get("error", {}).get("message", "").lower().find("not allowlisted") >= 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_data_file_download_is_forbidden(client: httpx.AsyncClient):
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    # Upload a tiny file with purpose=user_data
    data = {"purpose": "user_data"}
    files = {
        "file": ("relay_ping.txt", b"ping", "text/plain"),
    }

    r = await client.post("/v1/files", headers=RELAY_AUTH_HEADER, data=data, files=files)
    r.raise_for_status()
    file_obj = r.json()
    file_id = file_obj["id"]

    # Metadata is allowed
    r = await client.get(f"/v1/files/{file_id}", headers=RELAY_AUTH_HEADER)
    r.raise_for_status()

    # Content download is forbidden upstream for user_data (expected current behavior)
    r = await client.get(f"/v1/files/{file_id}/content", headers=RELAY_AUTH_HEADER)
    assert r.status_code == 400, r.text
    body = r.json()
    msg = body.get("error", {}).get("message", "")
    assert "not allowed" in msg.lower()
    assert "user_data" in msg.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_batch_output_file_is_downloadable(client: httpx.AsyncClient):
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    # Create a minimal batch input JSONL file in-memory
    jsonl_line = json.dumps(
        {
            "custom_id": "ping-1",
            "method": "POST",
            "url": "/v1/responses",
            "body": {"model": "gpt-5.1", "input": "Return exactly: pong"},
        }
    ).encode("utf-8") + b"\n"

    # Upload batch input
    data = {"purpose": "batch"}
    files = {"file": ("batch_input.jsonl", jsonl_line, "application/jsonl")}
    r = await client.post("/v1/files", headers=RELAY_AUTH_HEADER, data=data, files=files)
    r.raise_for_status()
    input_file_id = r.json()["id"]

    # Create batch
    r = await client.post(
        "/v1/batches",
        headers={**RELAY_AUTH_HEADER, "Content-Type": "application/json"},
        json={
            "input_file_id": input_file_id,
            "endpoint": "/v1/responses",
            "completion_window": "24h",
        },
    )
    r.raise_for_status()
    batch_id = r.json()["id"]

    # Poll until terminal
    final = await _poll_batch_until_terminal(client, batch_id=batch_id, timeout_seconds=240)

    assert final.get("status") == "completed", final
    out_file_id = final.get("output_file_id")
    assert out_file_id, final

    # Download output content
    r = await client.get(f"/v1/files/{out_file_id}/content", headers=RELAY_AUTH_HEADER)
    r.raise_for_status()

    # Response is JSONL; assert expected payload appears
    text = r.content.decode("utf-8", errors="replace")
    assert "pong" in text.lower()
