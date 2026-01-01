"""Integration smoke test for realtime WS relay."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlparse

import pytest
import requests
import websockets
from websockets.exceptions import ConnectionClosed

RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
RELAY_TOKEN = os.getenv("RELAY_TOKEN") or os.getenv("RELAY_KEY") or os.getenv("RELAY_AUTH_TOKEN")
DEFAULT_TIMEOUT_S = float(os.getenv("RELAY_TEST_TIMEOUT_S", "30"))
REALTIME_MODEL = os.getenv("RELAY_REALTIME_MODEL", "gpt-realtime")
INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"


def _bool_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _auth_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if RELAY_TOKEN:
        headers["Authorization"] = f"Bearer {RELAY_TOKEN}"
    if extra:
        headers.update(extra)
    return headers


def _ws_headers() -> list[tuple[str, str]]:
    headers: list[tuple[str, str]] = []
    if RELAY_TOKEN:
        headers.append(("Authorization", f"Bearer {RELAY_TOKEN}"))
    return headers


def _skip_if_realtime_disabled() -> None:
    if not _bool_env("RELAY_REALTIME_WS_ENABLED"):
        pytest.skip("Set RELAY_REALTIME_WS_ENABLED=1 to run realtime WS integration tests")


def _skip_if_missing_integration_key() -> None:
    if not _bool_env(INTEGRATION_ENV_VAR):
        pytest.skip(f"Set {INTEGRATION_ENV_VAR}=1 to run realtime WS integration tests")


def _get_health() -> Dict[str, Any]:
    response = requests.get(
        f"{RELAY_BASE_URL}/v1/health",
        timeout=DEFAULT_TIMEOUT_S,
    )
    if response.status_code != 200:
        pytest.skip(f"Relay health check failed: {response.status_code}")
    return response.json()


def _skip_if_missing_credentials(health: Dict[str, Any]) -> None:
    relay_info = health.get("relay", {})
    auth_enabled = bool(relay_info.get("auth_enabled"))
    if auth_enabled and not RELAY_TOKEN:
        pytest.skip("Relay auth is enabled but no RELAY_TOKEN/RELAY_KEY provided")

    openai_info = health.get("openai", {})
    if not bool(openai_info.get("api_key_configured")):
        pytest.skip("Relay is missing OPENAI_API_KEY; realtime sessions unavailable")


def _extract_client_secret(data: Dict[str, Any]) -> str:
    secret = data.get("client_secret")
    if isinstance(secret, str) and secret:
        return secret
    if isinstance(secret, dict):
        for key in ("value", "secret", "token"):
            value = secret.get(key)
            if isinstance(value, str) and value:
                return value
    for key in ("client_secret", "secret", "token"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    raise AssertionError("No client_secret (or equivalent token) returned from realtime session")


def _build_ws_url(model: str, session_id: Optional[str]) -> str:
    parsed = urlparse(RELAY_BASE_URL)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    base_path = parsed.path.rstrip("/")
    ws_base = f"{scheme}://{parsed.netloc}{base_path}"
    params = {"model": model}
    if session_id:
        params["session_id"] = session_id
    return f"{ws_base}/v1/realtime/ws?{urlencode(params)}"


async def _probe_ws(ws_url: str) -> Dict[str, Any]:
    event: Dict[str, Any] = {}
    try:
        async with websockets.connect(
            ws_url,
            extra_headers=_ws_headers(),
            subprotocols=["openai-realtime-v1"],
            open_timeout=DEFAULT_TIMEOUT_S,
        ) as websocket:
            init_event = {"type": "session.update", "session": {"modalities": ["text"]}}
            await websocket.send(json.dumps(init_event))

            try:
                raw = await asyncio.wait_for(websocket.recv(), timeout=5)
            except asyncio.TimeoutError:
                await asyncio.sleep(0.5)
                if websocket.closed:
                    raise AssertionError(
                        f"Realtime WS closed early with code {websocket.close_code}"
                    )
                return {}

            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                event = {"raw": raw}

            return event
    except ConnectionClosed as exc:
        raise AssertionError(f"Realtime WS connection closed with code {exc.code}") from exc


@pytest.mark.integration
def test_realtime_ws_session_smoke() -> None:
    _skip_if_realtime_disabled()
    _skip_if_missing_integration_key()

    health = _get_health()
    _skip_if_missing_credentials(health)

    payload = {"model": REALTIME_MODEL}
    response = requests.post(
        f"{RELAY_BASE_URL}/v1/realtime/sessions",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert response.status_code == 200, (
        f"/v1/realtime/sessions returned {response.status_code}: {response.text[:400]}"
    )

    data = response.json()
    client_secret = _extract_client_secret(data)
    assert client_secret

    session_id = data.get("id") or data.get("session_id")
    ws_url = _build_ws_url(REALTIME_MODEL, session_id if isinstance(session_id, str) else None)

    event = asyncio.run(_probe_ws(ws_url))
    if event:
        event_type = event.get("type")
        if event_type in {"error", "session.error"} or "error" in event:
            raise AssertionError(f"Realtime WS error event: {event}")