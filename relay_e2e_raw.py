#!/usr/bin/env python
"""
relay_e2e_raw.py — Unified E2E test for ChatGPT Team Relay (HTTP + Realtime WS)

This script exercises the relay in two layers:

  1) Core HTTP tests against OpenAI-compatible surfaces:
       - /health
       - /v1/responses  (non-stream + SSE stream)
       - /v1/embeddings
       - /v1/models
       - /v1/files              (best-effort)
       - /v1/vector_stores      (best-effort)
       - /v1/images             (best-effort)
       - /v1/videos             (best-effort)
       - /v1/conversations      (best-effort)
       - /v1/tools              (best-effort)
       - /v1/realtime/sessions  (HTTP best-effort)

  2) Realtime WebSocket test, via OpenAI Realtime:
       - POST /v1/realtime/sessions on the relay
       - Connect WebSocket to OpenAI's Realtime URL using client_secret
       - Send input_text event "Say exactly: relay-ws-ok"
       - Aggregate response.output_text.delta messages
       - Assert final text == "relay-ws-ok"

Environment variables:

  REST_BASE   — base URL for the relay, e.g. https://chatgpt-team-relay.onrender.com
  API_BASE    — optional override for /v1 API base (default: REST_BASE + "/v1")
  RELAY_KEY   — relay bearer key (must match relay's RELAY_KEY)
  DEBUG       — "1"/"true"/"yes" for verbose logs

Dependencies:

  pip install requests websockets
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, Iterable, Tuple

import requests

try:
    import websockets
except ImportError:
    websockets = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Environment & URL utilities
# ---------------------------------------------------------------------------

REST_BASE = os.environ.get("REST_BASE", "https://chatgpt-team-relay.onrender.com").rstrip(
    "/"
)
_API_BASE_ENV = os.environ.get("API_BASE")
if _API_BASE_ENV:
    API_BASE = _API_BASE_ENV.rstrip("/")
else:
    API_BASE = REST_BASE + "/v1"

RELAY_KEY = os.environ.get("RELAY_KEY", "dummy")
DEBUG = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")


def _dbg(msg: str) -> None:
    if DEBUG:
        print(f"[relay-e2e] [DEBUG] {msg}", file=sys.stderr)


def _build_url(path: str) -> str:
    """
    Build a URL for the relay, mirroring the semantics used in the original
    E2E script:

      - /health           → REST_BASE + "/health"
      - /relay/...        → REST_BASE + "/relay/..."
      - /v1/... and others:
           API_BASE is the default base for /v1:
             • If API_BASE endswith "/v1" and path startswith "/v1/":
                 drop the leading "/v1" from path to avoid "/v1/v1" duplication.
             • Else: use path as-is.
    """
    if not path.startswith("/"):
        path = "/" + path

    if path == "/health" or path.startswith("/relay/"):
        return f"{REST_BASE}{path}"

    base = API_BASE.rstrip("/")
    if base.endswith("/v1") and path.startswith("/v1/"):
        normalized_path = path[3:]  # remove leading "/v1"
    else:
        normalized_path = path

    return f"{base}{normalized_path}"


def _headers_json() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {RELAY_KEY}",
        "Content-Type": "application/json",
    }


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {RELAY_KEY}",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# ---------------------------------------------------------------------------
# Core HTTP tests
# ---------------------------------------------------------------------------

def test_health() -> None:
    _print_section("TEST: /health")
    url = _build_url("/health")
    _dbg(f"GET {url}")
    resp = requests.get(url, timeout=15.0)
    print(f"GET /health -> HTTP {resp.status_code}")
    _require(resp.status_code == 200, "Expected HTTP 200 from /health")

    try:
        data = resp.json()
    except Exception:
        raise AssertionError("Health endpoint did not return valid JSON")

    _dbg(f"Health payload: {json.dumps(data, indent=2)}")
    _require(data.get("status") == "ok", "Health status is not 'ok'")


def test_responses_non_stream(model: str = "gpt-4o-mini") -> None:
    _print_section("TEST: /v1/responses (non-stream)")
    url = _build_url("/v1/responses")
    headers = _headers_json()
    body = {
        "model": model,
        "input": "Say exactly: relay-http-ok",
    }

    _dbg(f"POST {url} body={body}")
    resp = requests.post(url, headers=headers, json=body, timeout=60.0)
    print(f"POST /v1/responses (non-stream) -> HTTP {resp.status_code}")
    _require(resp.status_code == 200, "Expected HTTP 200 from /v1/responses")

    try:
        data = resp.json()
    except Exception:
        raise AssertionError("Non-stream /v1/responses did not return valid JSON")

    _dbg(f"/v1/responses (non-stream) payload: {json.dumps(data, indent=2)}")

    # The exact structure may vary, but the common pattern for the Responses API is:
    #   data["output"][0]["content"][0]["text"]
    output_text = None
    try:
        output = data.get("output") or data.get("response") or []
        if isinstance(output, list) and output:
            content = output[0].get("content") or []
            if isinstance(content, list) and content:
                output_text = content[0].get("text")
    except Exception:
        output_text = None

    _require(
        isinstance(output_text, str) and "relay-http-ok" in output_text,
        "Expected non-stream responses output to contain 'relay-http-ok'",
    )
    print("Non-stream /v1/responses OK")


def _iter_sse_lines(resp: requests.Response) -> Iterable[str]:
    """
    Iterate over SSE lines from a streaming response.

    Lines typically look like:
      "data: {...json...}\n\n"
    """
    for raw_line in resp.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        yield raw_line


def test_responses_stream(model: str = "gpt-4o-mini") -> None:
    _print_section("TEST: /v1/responses (stream)")
    url = _build_url("/v1/responses")
    headers = _headers_json()
    body = {
        "model": model,
        "input": "Say exactly: relay-stream-ok",
        "stream": True,
    }

    _dbg(f"POST {url} body={body} (stream=True)")
    resp = requests.post(url, headers=headers, json=body, stream=True, timeout=120.0)
    print(f"POST /v1/responses (stream) -> HTTP {resp.status_code}")
    _require(
        resp.status_code == 200,
        "Expected HTTP 200 from streaming /v1/responses",
    )

    aggregated = []
    started = time.time()
    for line in _iter_sse_lines(resp):
        _dbg(f"SSE line: {line!r}")
        if not line.startswith("data:"):
            continue

        payload_str = line[5:].strip()
        if payload_str == "[DONE]":
            break

        try:
            event = json.loads(payload_str)
        except json.JSONDecodeError:
            _dbg("Skipping non-JSON SSE payload")
            continue

        # We expect Realtime-style deltas from the Responses API:
        #   { "type": "response.output_text.delta", "delta": "..." }
        if event.get("type") == "response.output_text.delta":
            delta = event.get("delta") or ""
            aggregated.append(delta)

        # Safety timeout
        if time.time() - started > 60:
            break

    text = "".join(aggregated).strip()
    print(f"Aggregated streaming text: {text!r}")
    _require(
        text.endswith("relay-stream-ok"),
        "Expected streaming output to end with 'relay-stream-ok'",
    )
    print("Stream /v1/responses OK")


def test_embeddings(model: str = "text-embedding-3-small") -> None:
    _print_section("TEST: /v1/embeddings")
    url = _build_url("/v1/embeddings")
    headers = _headers_json()
    body = {
        "model": model,
        "input": "Hello from relay embeddings E2E",
    }

    _dbg(f"POST {url} body={body}")
    resp = requests.post(url, headers=headers, json=body, timeout=60.0)
    print(f"POST /v1/embeddings -> HTTP {resp.status_code}")
    _require(resp.status_code == 200, "Expected HTTP 200 from /v1/embeddings")

    data = resp.json()
    _dbg(f"/v1/embeddings payload: {json.dumps(data, indent=2)}")

    embedding = None
    try:
        arr = data.get("data") or []
        if isinstance(arr, list) and arr:
            embedding = arr[0].get("embedding")
    except Exception:
        embedding = None

    _require(
        isinstance(embedding, list) and len(embedding) > 0,
        "Expected first embedding to be a non-empty list",
    )
    print("Embeddings OK")


def test_models() -> None:
    _print_section("TEST: /v1/models")
    url = _build_url("/v1/models")
    headers = _headers()
    _dbg(f"GET {url}")
    resp = requests.get(url, headers=headers, timeout=30.0)
    print(f"GET /v1/models -> HTTP {resp.status_code}")
    _require(resp.status_code == 200, "Expected HTTP 200 from /v1/models")

    data = resp.json()
    _dbg(f"/v1/models payload: {json.dumps(data, indent=2)}")

    _require(
        isinstance(data.get("data"), list),
        "Expected /v1/models to return a 'data' list",
    )
    print("Models OK")


# ---------------------------------------------------------------------------
# Best-effort HTTP tests (do not fail suite on error)
# ---------------------------------------------------------------------------

def best_effort_get(path: str, label: str) -> None:
    url = _build_url(path)
    headers = _headers()
    _dbg(f"GET {url} (best-effort)")
    try:
        resp = requests.get(url, headers=headers, timeout=30.0)
        print(f"GET {path} -> HTTP {resp.status_code}")
    except Exception as exc:
        print(f"BEST-EFFORT {label}: ERROR contacting {path}: {exc}")
        return

    try:
        data = resp.json()
        _dbg(f"{path} payload: {json.dumps(data, indent=2)}")
    except Exception:
        print(f"BEST-EFFORT {label}: non-JSON response")


def test_best_effort_endpoints() -> None:
    _print_section("BEST-EFFORT: Misc endpoints")

    best_effort_get("/v1/files", "files")
    best_effort_get("/v1/vector_stores", "vector_stores")
    best_effort_get("/v1/images", "images")
    best_effort_get("/v1/videos", "videos")
    best_effort_get("/v1/conversations", "conversations")
    best_effort_get("/v1/tools", "tools")
    best_effort_get("/v1/realtime/sessions", "realtime.sessions")


# ---------------------------------------------------------------------------
# Realtime WebSocket test (combined here)
# ---------------------------------------------------------------------------

def create_realtime_session() -> Tuple[str, str]:
    """
    Step 1: Create a Realtime session via the relay.

    Returns:
        (client_secret_value, realtime_url)
    """
    _print_section("TEST: /v1/realtime/sessions (HTTP)")

    url = _build_url("/v1/realtime/sessions")
    headers = _headers_json()
    payload: Dict[str, Any] = {
        "model": "gpt-realtime-preview",
        "modalities": ["text"],
        "instructions": "You are a test assistant. Say exactly: relay-ws-ok",
        # Avoid session_ttl_seconds; some accounts 400 this.
    }

    _dbg(f"POST {url} payload={payload}")
    resp = requests.post(url, headers=headers, json=payload, timeout=60.0)
    print(f"POST /v1/realtime/sessions -> HTTP {resp.status_code}")

    try:
        data = resp.json()
    except Exception:
        print(
            "[relay-e2e] ERROR: Failed to decode JSON from /v1/realtime/sessions"
        )
        data = {}

    _dbg(f"/v1/realtime/sessions payload: {json.dumps(data, indent=2)}")

    if resp.status_code != 200:
        raise AssertionError(
            f"/v1/realtime/sessions did not return 200 (got {resp.status_code})"
        )

    client_secret = (
        data.get("client_secret", {}) or {}
    ).get("value")
    realtime_url = (data.get("realtime", {}) or {}).get("url")

    if not client_secret or not realtime_url:
        raise AssertionError(
            "Realtime session payload missing client_secret.value or realtime.url"
        )

    print(
        "[relay-e2e] Realtime session OK; got client_secret (***hidden***) "
        f"and realtime.url={realtime_url!r}"
    )
    return client_secret, realtime_url


async def _ws_roundtrip(client_secret: str, realtime_url: str) -> bool:
    """
    Step 2: WebSocket roundtrip to OpenAI Realtime:

      - Connect to realtime_url with Authorization: Bearer <client_secret>.
      - Send input_text: 'Say exactly: relay-ws-ok'.
      - Aggregate response.output_text.delta events.
      - Expect final text == 'relay-ws-ok'.
    """
    if websockets is None:
        print("[relay-e2e] websockets library not installed; skipping WS test.")
        return False

    headers = {
        "Authorization": f"Bearer {client_secret}",
    }

    _dbg(f"Connecting WebSocket to {realtime_url} with Authorization header")

    async with websockets.connect(realtime_url, extra_headers=headers) as ws:
        message = {
            "type": "input_text",
            "text": "Say exactly: relay-ws-ok",
        }
        await ws.send(json.dumps(message))
        _dbg(f"Sent input_text message: {message}")

        text_chunks: list[str] = []
        expected = "relay-ws-ok"
        start = time.time()

        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=20.0)
            except asyncio.TimeoutError:
                print("[relay-e2e] ERROR: Timed out waiting for WS response.")
                return False

            _dbg(f"WS frame: {raw!r}")

            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                _dbg("Non-JSON WS frame; ignoring")
                continue

            if obj.get("type") == "response.output_text.delta":
                delta = obj.get("delta", "")
                text_chunks.append(delta)
                if "".join(text_chunks).strip().endswith(expected):
                    break

            if time.time() - start > 60:
                print("[relay-e2e] ERROR: WS response timeout.")
                return False

    aggregated = "".join(text_chunks).strip()
    print(f"[relay-e2e] Aggregated WS text: {aggregated!r}")

    if aggregated != expected:
        print(
            "[relay-e2e] ERROR: Expected WS text "
            f"{expected!r}, got {aggregated!r}"
        )
        return False

    return True


def test_realtime_ws() -> None:
    _print_section("TEST: Realtime WebSocket (via OpenAI)")

    if websockets is None:
        print(
            "[relay-e2e] websockets not installed; "
            "install with `pip install websockets` to run this test."
        )
        return

    client_secret, realtime_url = create_realtime_session()
    ok = asyncio.run(_ws_roundtrip(client_secret, realtime_url))

    if ok:
        print("Realtime WS test PASSED.")
    else:
        raise AssertionError("Realtime WS test FAILED.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=== ChatGPT Team Relay E2E (HTTP + Realtime WS) ===")
    print(f"REST_BASE={REST_BASE}")
    print(f"API_BASE={API_BASE}")
    print(f"DEBUG={DEBUG}")
    print()

    try:
        # Core HTTP tests (hard failures)
        test_health()
        test_responses_non_stream()
        test_responses_stream()
        test_embeddings()
        test_models()

        # Best-effort extras (never fail the suite)
        test_best_effort_endpoints()

        # Realtime WebSocket test (hard failure if websockets is available)
        test_realtime_ws()

    except AssertionError as exc:
        print()
        print("E2E: FAILED.")
        print(f"Reason: {exc}")
        return 1
    except Exception as exc:
        print()
        print("E2E: FAILED (unhandled exception).")
        print(f"Reason: {exc}")
        return 1

    print()
    print("E2E: ALL TESTS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
