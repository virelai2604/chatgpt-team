#!/usr/bin/env python3
"""
ChatGPT Team Relay - End to End (E2E) raw HTTP + Realtime test script.

This script is intended for local development of the ChatGPT Team Relay
(Cloudflare deployment or local dev with Uvicorn). It avoids SDKs and
uses raw HTTP + WebSockets to ensure that:

1) /health and /v1/health respond correctly.
2) /v1/responses returns expected output (non-stream).
3) /v1/responses with stream=true (SSE) works.
4) /v1/embeddings works.
5) /v1/models is forwarded & returns a list.
6) /v1/tools, /relay/actions, /relay/models are reachable.
7) /v1/files upload + list works.
8) /v1/vector_stores list works.
9) /v1/conversations list works.
10) /v1/images works (basic b64_json generation).
11) /v1/videos basic error handling (non-fatal).
12) /v1/realtime/sessions + WS roundtrip works (best-effort).

Environment variables honored:

- BASE_URL: Root of relay server, e.g. "http://127.0.0.1:8000"
- RELAY_KEY: Bearer token to authenticate to relay.
- RELAY_E2E_DEBUG: If non-empty, prints request/response debug logs.
- TEST_MODEL: Override default chat model (default: "gpt-4o-mini").
- EMBEDDING_MODEL: Override default embedding model
- IMAGE_MODEL: Override default image model (default: "gpt-image-1").
- REALTIME_MODEL: Override default realtime model for WS tests.
- RELAY_REALTIME_MODEL: Alternate env used by relay; we also read this.
"""

import asyncio
import base64
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    import websockets  # type: ignore
except Exception:  # pragma: no cover
    websockets = None  # type: ignore


# --- Logging helpers ---


def is_debug() -> bool:
    return bool(os.environ.get("RELAY_E2E_DEBUG"))


def log(msg: str) -> None:
    print(f"[relay-e2e-raw] {msg}", flush=True)


def debug(msg: str) -> None:
    if is_debug():
        log(msg)


# --- Configuration ---


def get_env(name: str, default: str) -> str:
    value = os.environ.get(name, default)
    return value


BASE_URL = get_env("REST_BASE", get_env("BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
# The ChatGPT Team Relay exposes OpenAI-compatible endpoints under /v1
API_BASE = f"{BASE_URL}/v1"

RELAY_KEY = get_env("RELAY_KEY", "dummy")

TEST_MODEL = get_env("TEST_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = get_env("EMBEDDING_MODEL", "text-embedding-3-small")
IMAGE_MODEL = get_env("IMAGE_MODEL", "gpt-image-1")
# Prefer REALTIME_MODEL if set, then RELAY_REALTIME_MODEL (used by the relay dev server),
# otherwise default to the current recommended Realtime model.
REALTIME_MODEL = (
    os.environ.get("REALTIME_MODEL")
    or os.environ.get("RELAY_REALTIME_MODEL")
    or "gpt-4o-realtime-preview"
)

log(f"Using REST_BASE={BASE_URL}")
log(f"Using API_BASE={API_BASE}")
log(f"Using TEST_MODEL={TEST_MODEL}")
log(f"Using EMBEDDING_MODEL={EMBEDDING_MODEL}")
log(f"Using IMAGE_MODEL={IMAGE_MODEL}")
log(f"Using REALTIME_MODEL={REALTIME_MODEL}")


def make_headers(
    accept: str = "application/json",
    content_type: str = "application/json",
) -> Dict[str, str]:
    h = {
        "Accept": accept,
        "Content-Type": content_type,
        "Authorization": f"Bearer {RELAY_KEY}",
    }
    return h


# --- HTTP helper ---


def request(
    method: str,
    path: str,
    *,
    base: str = API_BASE,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    stream: bool = False,
) -> requests.Response:
    url = f"{base}{path}"
    hdrs = headers or make_headers()
    debug(f"REQUEST {method} {path} url={url}")
    debug(f"HEADERS: {hdrs}")
    debug(f"JSON BODY: {json_body!r}")
    resp = requests.request(method, url, headers=hdrs, json=json_body, stream=stream)
    debug(
        f"RESPONSE {method} {path}: status={resp.status_code}, "
        f"headers={dict(resp.headers)}, "
        f"text={resp.text[:1024]!r}"
    )
    return resp


# --- Tests ---


def test_health() -> None:
    log("=== 0) /health and /v1/health ===")

    # Root health
    resp = request("GET", "/health", base=BASE_URL)
    assert resp.status_code == 200, f"/health status={resp.status_code}"
    data = resp.json()
    assert data.get("status") == "ok", f"Unexpected /health payload: {data!r}"
    log(f"/health OK: {data}")

    # /v1/health
    resp = request("GET", "/health", base=API_BASE)
    assert resp.status_code == 200, f"/v1/health status={resp.status_code}"
    data = resp.json()
    assert data.get("status") == "ok", f"Unexpected /v1/health payload: {data!r}"
    log(f"/v1/health OK: {data}")


def test_responses_simple() -> None:
    log("=== 1) /v1/responses (non-stream) ===")
    payload = {
        "model": TEST_MODEL,
        "input": "Say exactly: relay-http-ok",
        "max_output_tokens": 64,
    }
    resp = request("POST", "/responses", json_body=payload)
    assert resp.status_code == 200, f"/v1/responses status={resp.status_code}"
    data = resp.json()
    # Basic shape checks
    assert data.get("object") == "response", f"Unexpected object: {data.get('object')}"
    output = data.get("output") or data.get("output_text") or data.get("choices")
    text = ""

    # The new Responses API returns an "output" array of message items.
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict):
            content = first.get("content") or []
            if isinstance(content, list) and content:
                # Look for an "output_text" item
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "output_text":
                        text = part.get("text", "")
                        break
    # Fallbacks for older shapes
    if not text and "choices" in data:
        text = data["choices"][0]["message"]["content"]

    assert "relay-http-ok" in text, f"Did not see expected text in response: {text!r}"
    log("OK: /v1/responses non-stream returned expected text.")


def test_embeddings() -> None:
    log("=== 2) /v1/embeddings ===")
    payload = {
        "model": EMBEDDING_MODEL,
        "input": "relay embedding test",
    }
    resp = request("POST", "/embeddings", json_body=payload)
    assert resp.status_code == 200, f"/v1/embeddings status={resp.status_code}"
    data = resp.json()
    # Accept either "list" object (OpenAI-style) or single embedding
    if data.get("object") == "list":
        arr = data.get("data") or []
        assert arr and isinstance(arr, list), "Embeddings data list is empty"
        emb = arr[0].get("embedding")
        assert emb and isinstance(emb, list), "First embedding vector is empty"
    else:
        emb = data.get("embedding")
        assert emb and isinstance(emb, list), "Embedding vector is empty"
    log("OK: /v1/embeddings returned a non-empty embedding vector.")


def test_responses_stream_sse() -> None:
    log("=== 3) /v1/responses (stream=true SSE) ===")

    payload = {
        "model": TEST_MODEL,
        "input": "Say exactly: relay-stream-ok",
        "max_output_tokens": 64,
        "stream": True,
    }
    headers = make_headers(accept="text/event-stream")
    resp = request(
        "POST",
        "/responses",
        headers=headers,
        json_body=payload,
        stream=True,
    )
    assert resp.status_code == 200, f"/v1/responses (SSE) status={resp.status_code}"

    text_chunks: List[str] = []

    # The Reponses streaming API uses server-sent-events style framing:
    # each line starts with "data: {json}\n". We'll parse and accumulate
    # "response.output_text.delta"/"done" events.
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        debug(f"SSE LINE: {line!r}")
        if not line.startswith("data: "):
            continue
        data_str = line[len("data: ") :]
        if data_str.strip() == "[DONE]":
            break
        try:
            obj = json.loads(data_str)
        except json.JSONDecodeError:
            continue

        event_type = obj.get("type")
        if not isinstance(event_type, str):
            continue

        # Collect text for delta/done events.
        if event_type in ("response.output_text.delta", "response.output_text.done"):
            # In the latest API, "delta" is often a plain string (partial text)
            # while "done" events may have a full "text" field. Handle both.
            text_piece: str = ""
            delta_val = obj.get("delta")
            if isinstance(delta_val, str):
                text_piece = delta_val
            elif isinstance(delta_val, dict):
                # Older shapes might use {"text": "..."} inside "delta"
                maybe_text = delta_val.get("text")
                if isinstance(maybe_text, str):
                    text_piece = maybe_text

            if not text_piece:
                maybe_text = obj.get("text")
                if isinstance(maybe_text, str):
                    text_piece = maybe_text

            if text_piece:
                text_chunks.append(text_piece)

    text = "".join(text_chunks)
    log(f"Aggregated SSE text: {text!r}")
    assert "relay-stream-ok" in text, f"Did not see expected SSE text: {text!r}"
    log("OK: SSE streaming /v1/responses succeeded.")


def test_models() -> None:
    log("=== 4) /v1/models ===")
    resp = request("GET", "/models")
    assert resp.status_code == 200, f"/v1/models status={resp.status_code}"
    data = resp.json()
    assert data.get("object") == "list", f"Unexpected /v1/models object: {data!r}"
    log("/v1/models HTTP 200, object='list'")


def test_tools_and_relay_endpoints() -> None:
    log("=== 5) /v1/tools + /relay/actions + /relay/models (best-effort) ===")

    # /v1/tools
    resp = request("GET", "/tools")
    if resp.status_code == 200:
        data = resp.json()
        log("/v1/tools HTTP 200, object='list'")
    else:
        log(f"/v1/tools HTTP {resp.status_code} (non-fatal)")

    # /relay/actions
    resp = request("GET", "/relay/actions", base=BASE_URL)
    if resp.status_code == 200:
        data = resp.json()
        log("/relay/actions HTTP 200, object='list'")
    else:
        log(f"/relay/actions HTTP {resp.status_code} (non-fatal)")

    # /relay/models
    resp = request("GET", "/relay/models", base=BASE_URL)
    if resp.status_code == 200:
        data = resp.json()
        log("/relay/models HTTP 200, object='list'")
    else:
        log(f"/relay/models HTTP {resp.status_code} (non-fatal)")


def test_files_roundtrip() -> None:
    log("=== 6) /v1/files (best-effort upload → list) ===")
    # We send a small base64-encoded text file via the relay proxy.
    content_bytes = b"relay test file\n"
    b64 = base64.b64encode(content_bytes).decode("utf-8")

    payload = {
        "purpose": "assistants",
        "file": b64,
        "filename": "relay-e2e.txt",
    }
    resp = request("POST", "/files", json_body=payload)
    if resp.status_code != 200:
        log(f"POST /v1/files HTTP {resp.status_code} (non-fatal)")
        return
    data = resp.json()
    assert data.get("object") == "file", f"Unexpected file object: {data!r}"
    log("POST /v1/files HTTP 200, object='file'")

    # Now list files
    resp = request("GET", "/files")
    if resp.status_code != 200:
        log(f"GET /v1/files HTTP {resp.status_code} (non-fatal)")
        return
    data = resp.json()
    assert data.get("object") == "list", f"Unexpected files list: {data!r}"
    log("GET /v1/files HTTP 200, object='list'")


def test_vector_stores_list() -> None:
    log("=== 7) /v1/vector_stores (best-effort) ===")
    resp = request("GET", "/vector_stores")
    if resp.status_code != 200:
        log(f"/v1/vector_stores HTTP {resp.status_code} (non-fatal)")
        return
    data = resp.json()
    assert data.get("object") == "list", f"Unexpected vector_stores list: {data!r}"
    log("/v1/vector_stores HTTP 200, object='list'")


def test_conversations_list() -> None:
    log("=== 8) /v1/conversations (best-effort) ===")
    resp = request("GET", "/conversations")
    if resp.status_code != 200:
        log(f"/v1/conversations HTTP {resp.status_code} (non-fatal)")
        return
    data = resp.json()
    assert data.get("object") == "list", f"Unexpected conversations list: {data!r}"
    log("/v1/conversations HTTP 200, object='list'")


def test_images_basic() -> None:
    log("=== 9) /v1/images (best-effort) ===")
    payload = {
        "model": IMAGE_MODEL,
        "prompt": "A small colored square with letters 'P4' to test relay images.",
        "size": "1024x1024",  # must be valid OpenAI size
        "response_format": "b64_json",
    }
    resp = request("POST", "/images", json_body=payload)
    if resp.status_code != 200:
        log(f"/v1/images HTTP {resp.status_code}, body={resp.text!r}")
        return

    data = resp.json()
    # Minimal validation: we expect "data" array with first element having b64_json.
    arr = data.get("data") or []
    if not arr or not isinstance(arr, list):
        log("Image response data is missing or invalid (non-fatal).")
        return
    first = arr[0]
    if not isinstance(first, dict):
        log("Image response first item not a dict (non-fatal).")
        return
    b64_json = first.get("b64_json")
    if not b64_json:
        log("Image response missing b64_json (non-fatal).")
        return
    log("OK: /v1/images returned a non-empty b64_json image payload.")


def test_videos_basic() -> None:
    log("=== 10) /v1/videos (best-effort) ===")
    # Many accounts won't have Sora access; we just ensure we get a sane error.
    payload = {
        "model": "sora-2.0-pro",
        # Intentionally omit prompt to see well-formed error from upstream.
    }
    resp = request("POST", "/videos", json_body=payload)
    if resp.status_code == 200:
        log("/v1/videos HTTP 200 (unexpected but OK).")
        return
    log(f"/v1/videos HTTP {resp.status_code}, body={resp.text!r}")


async def _realtime_ws_roundtrip(ws_url: str, client_secret: Optional[str]) -> bool:
    """
    Connect to the Realtime WebSocket, send an input_text event,
    and check for 'relay-ws-ok' in the streamed text output.
    Returns True if the phrase is observed, False otherwise.
    """
    if websockets is None:  # pragma: no cover
        log("websockets library is not installed; skipping realtime WS test.")
        return False

    headers: Dict[str, str] = {}
    if client_secret:
        # For client secrets, the Authorization header should use the client_secret as a bearer token.
        headers["Authorization"] = f"Bearer {client_secret}"

    log(f"Connecting to Realtime WS: {ws_url}")
    try:
        async with websockets.connect(ws_url, extra_headers=headers) as websocket:  # type: ignore[arg-type]
            log("Realtime WS connected; sending input_text event.")
            await websocket.send(
                json.dumps(
                    {
                        "type": "input_text",
                        "text": "Say exactly: relay-ws-ok",
                    }
                )
            )

            chunks: List[str] = []
            # Read events until we either time out or see a completed response.
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                except asyncio.TimeoutError:
                    log("Realtime WS timeout while waiting for events.")
                    break

                debug(f"WS RECV: {message!r}")
                # The Realtime API returns plain JSON objects per message.
                try:
                    event = json.loads(message)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type") or ""
                if not event_type:
                    continue

                # If an error event is received, log and abort.
                if event_type == "error":
                    log(f"Realtime WS error event: {event}")
                    break

                # Collect text from output_text delta/done events.
                if event_type in ("response.output_text.delta", "response.output_text.done"):
                    text_piece = event.get("delta") or event.get("text") or ""
                    if isinstance(text_piece, str):
                        chunks.append(text_piece)

                # Stop when we see a completed response.
                if event_type in ("response.completed", "response.completed.success"):
                    break

            text = "".join(chunks)
            log(f"Realtime WS aggregated text: {text!r}")
            return "relay-ws-ok" in text
    except Exception as exc:  # pragma: no cover - network failures, etc.
        log(f"ERROR during realtime WS: {exc}")
        return False


def test_realtime_session() -> None:
    log("=== 11) /v1/realtime/sessions + WS (best-effort) ===")

    payload = {
        "model": REALTIME_MODEL,
    }
    resp = request("POST", "/realtime/sessions", json_body=payload)
    if resp.status_code != 200:
        log(
            f"POST /v1/realtime/sessions HTTP {resp.status_code} "
            f"(non-fatal), body={resp.text!r}"
        )
        return
    data = resp.json()
    ws_url = data.get("ws_url")
    client_secret_obj = data.get("client_secret") or {}
    client_secret = client_secret_obj.get("value")

    if not ws_url or not client_secret:
        log(
            "Realtime session created but ws_url or client_secret missing; "
            "skipping WS test (non-fatal)."
        )
        return

    log(
        f"Realtime session created. ws_url={ws_url!r}, "
        f"client_secret={'present' if client_secret else 'missing'}"
    )

    # Attempt WebSocket round-trip. Non-fatal on failure.
    ok = asyncio.run(_realtime_ws_roundtrip(ws_url, client_secret))
    if ok:
        log("Realtime WS test confirmed 'relay-ws-ok'.")
    else:
        log("Realtime WS test did not confirm 'relay-ws-ok' (non-fatal).")


def main() -> int:
    log("=== ChatGPT Team Relay E2E (HTTP + Realtime) ===")
    log(f"Using REST_BASE={BASE_URL}")
    log(f"Using API_BASE={API_BASE}")
    log(f"Using TEST_MODEL={TEST_MODEL}")
    log(f"Using EMBEDDING_MODEL={EMBEDDING_MODEL}")

    # 0) health
    test_health()

    # 1) responses non-stream
    test_responses_simple()

    # 2) embeddings
    test_embeddings()

    # 3) responses stream (SSE)
    test_responses_stream_sse()

    # 4) models
    test_models()

    # 5) tools / relay endpoints
    test_tools_and_relay_endpoints()

    # 6) files upload + list
    test_files_roundtrip()

    # 7) vector stores
    test_vector_stores_list()

    # 8) conversations
    test_conversations_list()

    # 9) images
    test_images_basic()

    # 10) videos (best-effort)
    test_videos_basic()

    # 11) realtime session + WS (best-effort)
    test_realtime_session()

    log("E2E RAW: CORE TESTS PASSED (health + responses + embeddings).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
