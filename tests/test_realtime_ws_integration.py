from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlsplit, urlunsplit

import pytest
import requests
from websockets import connect as ws_connect


pytestmark = pytest.mark.integration

RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
RELAY_TOKEN = os.getenv("RELAY_TOKEN", "dummy")
REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-realtime")
DEFAULT_TIMEOUT_S = float(os.getenv("RELAY_TEST_TIMEOUT_S", "60"))


def _skip_if_no_real_key() -> None:
    if os.getenv("INTEGRATION_OPENAI_API_KEY") != "1":
        pytest.skip("INTEGRATION_OPENAI_API_KEY != 1 (skipping real-API integration tests)")


def _skip_if_ws_disabled() -> None:
    if os.getenv("RELAY_REALTIME_WS_ENABLED") != "1":
        pytest.skip("RELAY_REALTIME_WS_ENABLED != 1 (realtime WS disabled)")


def _auth_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {"Authorization": f"Bearer {RELAY_TOKEN}"}
    if extra:
        headers.update(extra)
    return headers


def _must_ok(r: requests.Response, *, hint: str = "") -> None:
    if r.ok:
        return
    body = r.text
    if len(body) > 4000:
        body = body[:4000] + "…(truncated)"
    raise AssertionError(f"{hint}HTTP {r.status_code} {r.reason}: {body}")


def _extract_client_secret(payload: Dict[str, Any]) -> Optional[str]:
    candidates = [
        payload.get("client_secret"),
        payload.get("client_secret_value"),
        payload.get("clientSecret"),
        payload.get("secret"),
        payload.get("token"),
    ]

    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = value.get("value") or value.get("secret") or value.get("token")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()

    return None


def _build_ws_url(model: str, session_id: Optional[str]) -> str:
    parts = urlsplit(RELAY_BASE_URL)
    scheme = "wss" if parts.scheme == "https" else "ws"
    base = urlunsplit((scheme, parts.netloc, "", "", ""))

    query_params = {"model": model}
    if session_id:
        query_params["session_id"] = session_id

    return f"{base}/v1/realtime/ws?{urlencode(query_params)}"


@pytest.mark.asyncio
async def test_realtime_session_and_ws_connect_smoke() -> None:
    _skip_if_no_real_key()
    _skip_if_ws_disabled()

    r = requests.post(
        f"{RELAY_BASE_URL}/v1/realtime/sessions",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={"model": REALTIME_MODEL},
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Create realtime session failed. ")
    payload = r.json()

    session_id = payload.get("id")
    assert isinstance(session_id, str) and session_id.strip(), "Missing session id in response"

    client_secret = _extract_client_secret(payload)
    ws_url = _build_ws_url(REALTIME_MODEL, session_id)

    headers: Dict[str, str] = {}
    if client_secret:
        headers["Authorization"] = f"Bearer {client_secret}"

    async with ws_connect(ws_url, extra_headers=headers) as websocket:
        await websocket.send(json.dumps({"type": "session.update", "session": {}}))
        first_msg = await asyncio.wait_for(websocket.recv(), timeout=10)
        assert first_msg is not None
