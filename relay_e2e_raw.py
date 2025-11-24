#!/usr/bin/env python3
"""
relay_e2e_raw.py — Unified E2E test for ChatGPT Team Relay (HTTP + Realtime WS)

End-to-end tests for the ChatGPT Team Relay using raw HTTP (requests),
manual brotli/gzip handling, and a basic Realtime WebSocket check.

Aligned with:
- API Reference - OpenAI API (responses, embeddings, files, images, videos, realtime)
- openai-python SDK 2.8.1 request shapes (responses.create, embeddings.create, etc.)

Environment:
  BASE_URL         – Base URL of the relay (e.g. https://chatgpt-team-relay.onrender.com)
  RELAY_KEY        – Bearer key for the relay (Authorization: Bearer <RELAY_KEY>)
  RELAY_E2E_DEBUG  – if non-empty, print verbose debug output

Core pass criteria:
  - /health and /v1/health
  - /v1/responses (non-stream)
  - /v1/embeddings

All other endpoints are "best-effort": they log status but do not flip core_ok.
"""

from __future__ import annotations

import asyncio
import base64
import gzip
import json
import os
import sys
from typing import Any, Dict, Iterable, Optional, Tuple

import requests

try:
    import brotli  # type: ignore
except ImportError:  # pragma: no cover
    brotli = None

try:
    import websockets  # type: ignore
except ImportError:  # pragma: no cover
    websockets = None


# ---------------------------------------------------------------------------
# Logging + environment helpers
# ---------------------------------------------------------------------------


def log(msg: str) -> None:
    print(f"[relay-e2e-raw] {msg}")


def debug(msg: str) -> None:
    if RELAY_E2E_DEBUG:
        print(f"[relay-e2e-raw] [DEBUG] {msg}", file=sys.stderr)


def get_env(name: str, default: str) -> str:
    val = os.environ.get(name, "").strip()
    return val or default


REST_BASE = get_env("BASE_URL", "https://chatgpt-team-relay.onrender.com").rstrip("/")
API_BASE = REST_BASE.rstrip("/") + "/v1"
RELAY_KEY = get_env("RELAY_KEY", "dummy")
RELAY_E2E_DEBUG = bool(os.environ.get("RELAY_E2E_DEBUG") or os.environ.get("DEBUG"))

TEST_MODEL = get_env("TEST_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = get_env("EMBEDDING_MODEL", "text-embedding-3-small")
IMAGE_MODEL = get_env("IMAGE_MODEL", "gpt-image-1")
REALTIME_MODEL = get_env("REALTIME_MODEL", "gpt-4.1-mini")  # or your realtime-capable model

log(f"Using REST_BASE={REST_BASE}")
log(f"Using API_BASE={API_BASE}")
log(f"Using TEST_MODEL={TEST_MODEL}")
log(f"Using EMBEDDING_MODEL={EMBEDDING_MODEL}")


# ---------------------------------------------------------------------------
# Low-level HTTP helpers
# ---------------------------------------------------------------------------


def maybe_decompress(content: bytes, headers: Dict[str, str]) -> bytes:
    """
    Try to decompress manually if:
    - Content-Encoding header is present (gzip, br), OR
    - JSON decode fails and we suspect compression.

    This is intentionally forgiving to cope with mislabelled Content-Encoding.
    """
    ce = headers.get("content-encoding", "").lower()
    if ce == "gzip":
        try:
            return gzip.decompress(content)
        except Exception:
            pass
    elif ce == "br":
        if brotli is not None:
            try:
                return brotli.decompress(content)
            except Exception:
                pass

    # Fallback heuristic: if it *looks* binary and JSON parse fails, try gzip+br.
    try:
        json.loads(content.decode("utf-8"))
        return content  # already plain JSON
    except Exception:
        pass

    # Try gzip
    try:
        return gzip.decompress(content)
    except Exception:
        pass

    # Try brotli
    if brotli is not None:
        try:
            return brotli.decompress(content)
        except Exception:
            pass

    return content


def _build_url(path: str) -> str:
    """
    Build URL for the relay.

    - /health, /relay/* → REST_BASE + path
    - /v1/*            → API_BASE + path, avoiding /v1/v1 duplication
    """
    if not path.startswith("/"):
        path = "/" + path

    if path == "/health" or path.startswith("/relay/"):
        return REST_BASE + path

    # OpenAI-style paths
    base = API_BASE.rstrip("/")
    if base.endswith("/v1") and path.startswith("/v1/"):
        # Avoid /v1/v1 duplication
        path = path[len("/v1") :]
    return base + path


def do_request(
    method: str,
    path: str,
    json_body: Optional[Dict[str, Any]] = None,
    *,
    accept: str = "application/json",
    timeout: float = 120.0,
) -> Tuple[int, Dict[str, Any], str]:
    """
    Perform a JSON-ish request.

    Returns (status_code, json_dict (or {}), raw_text).
    """
    url = _build_url(path)
    headers: Dict[str, str] = {
        "Accept": accept,
        "Content-Type": "application/json",
    }
    if RELAY_KEY:
        headers["Authorization"] = f"Bearer {RELAY_KEY}"

    debug(f"REQUEST {method} {path} url={url}")
    debug(f"HEADERS: {headers!r}")
    debug(f"JSON BODY: {json_body!r}")

    try:
        resp = requests.request(
            method,
            url,
            headers=headers,
            json=json_body,
            timeout=timeout,
        )
    except Exception as exc:
        log(f"ERROR: Exception during {method} {path}: {exc}")
        return 0, {}, ""

    status = resp.status_code
    raw_content = resp.content
    raw_headers = {k.lower(): v for k, v in resp.headers.items()}
    content = maybe_decompress(raw_content, raw_headers)
    try:
        text = content.decode("utf-8", errors="replace")
    except Exception:
        text = ""

    debug(
        f"RESPONSE {method} {path}: status={status}, headers={dict(resp.headers)}, "
        f"text={text[:500]!r}"
    )

    try:
        data = json.loads(text) if text else {}
    except json.JSONDecodeError:
        data = {}

    return status, data, text


def iter_sse_lines(
    path: str,
    json_body: Dict[str, Any],
    *,
    timeout: float = 120.0,
) -> Iterable[str]:
    """
    Stream SSE lines from /v1/responses with stream=true.
    """
    url = _build_url(path)
    headers: Dict[str, str] = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    if RELAY_KEY:
        headers["Authorization"] = f"Bearer {RELAY_KEY}"

    debug(f"SSE REQUEST POST {path} url={url}")
    debug(f"SSE HEADERS: {headers!r}")
    debug(f"SSE JSON BODY: {json_body!r}")

    with requests.post(url, headers=headers, json=json_body, stream=True, timeout=timeout) as resp:
        debug(f"SSE RESPONSE status={resp.status_code}, headers={dict(resp.headers)}")
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if line is None:
                continue
            yield line


# ---------------------------------------------------------------------------
# Core tests
# ---------------------------------------------------------------------------


def test_health() -> bool:
    log("=== 0) /health and /v1/health ===")
    ok = True

    for path in ("/health", "/v1/health"):
        status, data, _ = do_request("GET", path)
        if status != 200:
            log(f"ERROR: {path} returned HTTP {status} (expected 200)")
            ok = False
            continue
        if not isinstance(data, dict) or data.get("status") != "ok":
            log(f"ERROR: {path} payload missing or not status=='ok': {data!r}")
            ok = False
        else:
            log(f"{path} OK: {data!r}")

    return ok


def _extract_text_from_response_obj(obj: Dict[str, Any]) -> str:
    """
    Extract text for /v1/responses based on the API reference / SDK shapes.
    Prefer response.output[0].content[0].text or output_text.
    """
    # New Responses API shape:
    # {
    #   "output": [
    #     {
    #       "content": [
    #         {"type": "output_text", "text": {"value": "..." } }
    #       ]
    #     }
    #   ]
    # }
    output = obj.get("output") or obj.get("outputs")
    if isinstance(output, list) and output:
        first = output[0]
        content = first.get("content")
        if isinstance(content, list) and content:
            c0 = content[0]
            if isinstance(c0, dict):
                txt_obj = c0.get("text")
                if isinstance(txt_obj, dict) and "value" in txt_obj:
                    return str(txt_obj["value"])
                if "value" in c0:
                    return str(c0["value"])
    # Fallback: try a simple path
    if "output_text" in obj and isinstance(obj["output_text"], dict):
        v = obj["output_text"].get("value")
        if isinstance(v, str):
            return v
    return ""


def test_responses_simple() -> bool:
    log("=== 1) /v1/responses (non-stream) ===")
    body = {
        "model": TEST_MODEL,
        "input": "Say exactly: relay-http-ok",
        "max_output_tokens": 64,
    }
    status, data, text = do_request("POST", "/v1/responses", body)
    if status != 200:
        log(f"ERROR: /v1/responses HTTP {status}, body={text[:500]!r}")
        return False

    out_text = _extract_text_from_response_obj(data)
    if "relay-http-ok" not in out_text:
        log(f"ERROR: /v1/responses output did not contain 'relay-http-ok': {out_text!r}")
        return False

    log("OK: /v1/responses non-stream returned expected text.")
    return True


def test_embeddings() -> bool:
    log("=== 2) /v1/embeddings ===")
    body = {
        "model": EMBEDDING_MODEL,
        "input": "relay embedding test",
    }
    status, data, text = do_request("POST", "/v1/embeddings", body)
    if status != 200:
        log(f"ERROR: /v1/embeddings HTTP {status}, body={text[:500]!r}")
        return False

    arr = data.get("data")
    if not isinstance(arr, list) or not arr:
        log(f"ERROR: /v1/embeddings missing data array: {data!r}")
        return False

    embedding = arr[0].get("embedding") if isinstance(arr[0], dict) else None
    if not isinstance(embedding, list) or not embedding:
        log(f"ERROR: /v1/embeddings missing numeric embedding: {arr[0]!r}")
        return False

    log("OK: /v1/embeddings returned a non-empty embedding vector.")
    return True


# ---------------------------------------------------------------------------
# Streaming test
# ---------------------------------------------------------------------------


def test_responses_streaming() -> bool:
    log("=== 3) /v1/responses (stream=true SSE) ===")
    body = {
        "model": TEST_MODEL,
        "input": "Say exactly: relay-stream-ok",
        "max_output_tokens": 64,
        "stream": True,
    }

    text_chunks: list[str] = []
    try:
        for line in iter_sse_lines("/v1/responses", body):
            if not line:
                continue
            debug(f"SSE: {line!r}")
            if line.startswith("data: "):
                payload = line[len("data: ") :]
                if payload.strip() == "[DONE]":
                    break
                try:
                    obj = json.loads(payload)
                except Exception:
                    continue
                if obj.get("type") == "response.output_text.delta":
                    delta = obj.get("delta") or ""
                    if isinstance(delta, str):
                        text_chunks.append(delta)
    except Exception as exc:
        log(f"ERROR: exception during SSE: {exc}")
        return False

    final = "".join(text_chunks)
    log(f"Aggregated SSE text: {final!r}")
    if "relay-stream-ok" not in final:
        log("ERROR: streaming text did not contain 'relay-stream-ok'")
        return False

    log("OK: SSE streaming /v1/responses succeeded.")
    return True


# ---------------------------------------------------------------------------
# Best-effort tests
# ---------------------------------------------------------------------------


def test_models_list() -> None:
    log("=== 4) /v1/models ===")
    status, data, _ = do_request("GET", "/v1/models")
    log(f"/v1/models HTTP {status}, object={data.get('object')!r}")


def test_tools_and_agentic() -> None:
    log("=== 5) /v1/tools + /relay/actions + /relay/models (best-effort) ===")
    for path in ("/v1/tools", "/relay/actions", "/relay/models"):
        status, data, _ = do_request("GET", path)
        log(f"{path} HTTP {status}, object={data.get('object')!r}")


def test_files_chain() -> None:
    log("=== 6) /v1/files (best-effort upload → list) ===")
    body = {
        "purpose": "assistants",
        "file": base64.b64encode(b"relay test file").decode("ascii"),
        "filename": "relay-e2e.txt",
    }
    status, data, _ = do_request("POST", "/v1/files", body)
    log(f"POST /v1/files HTTP {status}, object={data.get('object')!r}")

    status, data, _ = do_request("GET", "/v1/files")
    log(f"GET /v1/files HTTP {status}, object={data.get('object')!r}")


def test_vector_stores_list() -> None:
    log("=== 7) /v1/vector_stores (best-effort) ===")
    status, data, _ = do_request("GET", "/v1/vector_stores")
    log(f"/v1/vector_stores HTTP {status}, object={data.get('object')!r}")


def test_conversations_list() -> None:
    log("=== 8) /v1/conversations (best-effort) ===")
    status, data, _ = do_request("GET", "/v1/conversations")
    log(f"/v1/conversations HTTP {status}, object={data.get('object')!r}")


def test_images_generation() -> None:
    log("=== 9) /v1/images (best-effort) ===")
    body = {
        "model": IMAGE_MODEL,
        "prompt": "A small colored square with letters 'P4' to test relay images.",
        "n": 1,
        "size": "512x512",
        "response_format": "b64_json",
    }
    status, data, text = do_request("POST", "/v1/images", body)
    if status == 200:
        try:
            first = (data.get("data") or [])[0]
            _ = first.get("b64_json")
            log("OK: /v1/images returned at least one b64_json image.")
        except Exception:
            log(f"/v1/images HTTP 200 but unexpected shape: {data!r}")
    else:
        # Build a safe log preview: prefer text, fall back to data repr
        preview = text[:500] if text else repr(data)
        log(f"/v1/images HTTP {status}, body={preview!r}")


def test_videos_short() -> None:
    log("=== 10) /v1/videos (best-effort) ===")
    body = {
        "model": TEST_MODEL,
        "input": "A short abstract test animation for relay sanity.",
        "seconds": "4",
    }
    status, data, text = do_request("POST", "/v1/videos", body)
    # Build a safe log preview: prefer text, fall back to data repr
    preview = text[:500] if text else repr(data)
    log(f"/v1/videos HTTP {status}, body={preview!r}")


# ---------------------------------------------------------------------------
# Realtime session + WebSocket (best-effort)
# ---------------------------------------------------------------------------


async def _realtime_ws_roundtrip(ws_url: str, client_secret: Optional[str]) -> bool:
    """
    Connect to the realtime WebSocket, send an input_text event,
    and check for 'relay-ws-ok' in output_text.delta events.
    """
    if websockets is None:
        log("websockets not installed; skipping realtime WS test.")
        return False

    headers: Dict[str, str] = {}
    if client_secret:
        headers["Authorization"] = f"Bearer {client_secret}"

    debug(f"Connecting WS to {ws_url} with headers={headers!r}")

    try:
        async with websockets.connect(ws_url, extra_headers=headers) as ws:
            event = {
                "type": "input_text",
                "content": "Say exactly: relay-ws-ok",
            }
            await ws.send(json.dumps(event))

            chunks: list[str] = []
            for _ in range(100):
                msg = await ws.recv()
                debug(f"WS recv: {msg!r}")
                try:
                    obj = json.loads(msg)
                except Exception:
                    continue

                if obj.get("type") == "response.output_text.delta":
                    delta = obj.get("delta") or ""
                    if isinstance(delta, str):
                        chunks.append(delta)
                if obj.get("type") in ("response.completed", "response.completed.success"):
                    break

            text = "".join(chunks)
            log(f"Realtime WS aggregated text: {text!r}")
            return "relay-ws-ok" in text
    except Exception as exc:
        log(f"ERROR during realtime WS: {exc}")
        return False


def test_realtime_session_and_ws() -> None:
    log("=== 11) /v1/realtime/sessions + WS (best-effort) ===")
    body = {
        "model": REALTIME_MODEL,
    }
    status, data, text = do_request("POST", "/v1/realtime/sessions", body)
    if status != 200:
        log(f"/v1/realtime/sessions HTTP {status}, body={text[:500]!r}")
        return

    ws_url = data.get("url") or data.get("ws_url") or ""
    client_secret = None
    cs = data.get("client_secret")
    if isinstance(cs, dict):
        client_secret = cs.get("value")

    if not ws_url:
        log(f"Realtime sessions response missing ws url: {data!r}")
        return

    log(
        f"Realtime session created. ws_url={ws_url!r}, "
        f"client_secret={'present' if client_secret else 'none'}"
    )

    try:
        ok = asyncio.run(_realtime_ws_roundtrip(ws_url, client_secret))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            ok = loop.run_until_complete(_realtime_ws_roundtrip(ws_url, client_secret))
        finally:
            loop.close()

    if ok:
        log("OK: realtime WS round-trip produced 'relay-ws-ok'.")
    else:
        log("Realtime WS test did not confirm 'relay-ws-ok' (non-fatal).")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    log("=== ChatGPT Team Relay E2E (HTTP + Realtime) ===")

    core_ok = True

    if not test_health():
        core_ok = False
    if not test_responses_simple():
        core_ok = False
    if not test_embeddings():
        core_ok = False

    if not test_responses_streaming():
        log("WARNING: streaming /v1/responses test failed (not flipping core_ok).")

    test_models_list()
    test_tools_and_agentic()
    test_files_chain()
    test_vector_stores_list()
    test_conversations_list()
    test_images_generation()
    test_videos_short()
    test_realtime_session_and_ws()

    if core_ok:
        log("E2E RAW: CORE TESTS PASSED (health + responses + embeddings).")
        return 0
    else:
        log("E2E RAW: CORE TESTS FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
