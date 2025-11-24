#!/usr/bin/env python
"""
relay_e2e_raw.py — End-to-end smoke test for ChatGPT Team Relay.

Covers:
  0) /health
  1) /v1/responses (non-stream + stream=true SSE)
  2) /v1/embeddings
  3) /v1/models
  4) /relay/models
  5) /v1/tools
  6) /v1/files
  7) /v1/vector_stores
  8) /v1/conversations
  9) /relay/actions
 10) /v1/realtime/sessions (basic JSON)
 11) /v1/images (best-effort)
 12) /v1/videos (best-effort)

Environment:
  REST_BASE   — root of relay, e.g. https://chatgpt-team-relay.onrender.com
  API_BASE    — base for /v1 APIs; if unset, defaults to REST_BASE + "/v1"
  RELAY_KEY   — must match RELAY_KEY configured on the relay
  DEBUG       — if truthy, prints verbose logs
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Iterable, List, Tuple

import requests

# ---------------------------------------------------------------------------
# Environment & base URLs
# ---------------------------------------------------------------------------

REST_BASE = os.environ.get("REST_BASE", "https://chatgpt-team-relay.example.com").rstrip(
    "/"
)
# API_BASE can be set explicitly; otherwise default to REST_BASE + "/v1"
_API_BASE_ENV = os.environ.get("API_BASE")
if _API_BASE_ENV:
    API_BASE = _API_BASE_ENV.rstrip("/")
else:
    API_BASE = REST_BASE + "/v1"

RELAY_KEY = os.environ.get("RELAY_KEY", "dummy")
DEBUG = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")

print(f"Using REST_BASE={REST_BASE}")
print(f"Using API_BASE={API_BASE}")
print(f"DEBUG={DEBUG}")


# ---------------------------------------------------------------------------
# Helper: URL construction
# ---------------------------------------------------------------------------


def _build_url(path: str) -> str:
    """
    Normalize path → full URL, avoiding /v1/v1 duplication.

    Rules:
      • /health and /relay/* go to REST_BASE directly.
      • All other test paths are treated as OpenAI-style endpoints, and we
        join them against API_BASE. If API_BASE already ends with "/v1"
        and path starts with "/v1/", we strip the additional "/v1" from
        the path to avoid "/v1/v1/...".
    """
    if not path:
        path = "/"
    if not path.startswith("/"):
        path = "/" + path

    # Root / health / relay-introspection → REST_BASE
    if path == "/health" or path.startswith("/relay/"):
        return f"{REST_BASE}{path}"

    # Everything else is considered under the OpenAI-style /v1 namespace.
    base = API_BASE.rstrip("/")

    if base.endswith("/v1") and path.startswith("/v1/"):
        # API_BASE already has /v1; strip the duplicate from path
        normalized_path = path[3:]  # drop the leading "/v1"
    else:
        normalized_path = path

    return f"{base}{normalized_path}"


# ---------------------------------------------------------------------------
# Core HTTP helper
# ---------------------------------------------------------------------------


def do_request(
    method: str, path: str, json_body: Dict[str, Any] | None
) -> Tuple[int, Dict[str, Any]]:
    url = _build_url(path)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RELAY_KEY}",
    }

    if DEBUG:
        print(f"[relay-e2e-raw] [DEBUG] REQUEST {method} {path} json_body={json_body}")
        print(f"[relay-e2e-raw] [DEBUG] REQUEST URL: {url}")
        print(f"[relay-e2e-raw] [DEBUG] REQUEST HEADERS: {headers}")

    resp = requests.request(method, url, headers=headers, json=json_body, timeout=60.0)

    if DEBUG:
        print(
            f"[relay-e2e-raw] [DEBUG] RESPONSE {method} {path}: "
            f"status={resp.status_code}, headers={dict(resp.headers)}, "
            f"text={resp.text!r}"
        )

    status_code = resp.status_code

    # Try to parse JSON defensively.
    try:
        data = resp.json()
    except Exception:
        if DEBUG:
            print(
                f"[relay-e2e-raw] [DEBUG] Failed to decode JSON from {method} {path}"
            )
        data = {}

    return status_code, data


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------


def _iter_sse_events(resp: requests.Response) -> Iterable[Tuple[str, str]]:
    """
    Parse a text/event-stream HTTP response into (event_type, data_str) tuples.

    We handle the standard SSE framing:
      event: <name>
      data: <json>
      <blank line>
    """
    event_type: str | None = None
    data_lines: List[str] = []

    for raw_line in resp.iter_lines(decode_unicode=True):
        if raw_line is None:
            continue

        line = raw_line.strip()
        if not line:
            if event_type and data_lines:
                yield event_type, "\n".join(data_lines)
            event_type, data_lines = None, []
            continue

        if line.startswith("event:"):
            event_type = line[len("event:") :].strip()
            if DEBUG:
                print(
                    f"[relay-e2e-raw] [DEBUG] SSE line: event: {event_type}",
                )
        elif line.startswith("data:"):
            payload = line[len("data:") :].strip()
            data_lines.append(payload)
            if DEBUG:
                print(
                    f"[relay-e2e-raw] [DEBUG] SSE line: data: {payload}",
                )

    if event_type and data_lines:
        yield event_type, "\n".join(data_lines)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_health() -> bool:
    print("=== 0) /health ===")
    status_code, resp_json = do_request("GET", "/health", None)
    print(f"[relay-e2e-raw] GET /health -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /health JSON: {resp_json}")

    if status_code != 200:
        print("[relay-e2e-raw] ERROR: /health did not return 200")
        return False

    if resp_json.get("status") != "ok":
        print("[relay-e2e-raw] ERROR: /health payload missing status='ok'")
        return False

    return True


def test_non_stream_responses() -> bool:
    print("=== 1a) /v1/responses (non-stream) ===")
    payload = {
        "model": "gpt-4o-mini",
        "input": "Say exactly: relay-http-ok",
        "max_output_tokens": 64,
    }
    status_code, resp_json = do_request("POST", "/v1/responses", payload)
    print(f"[relay-e2e-raw] POST /v1/responses -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /v1/responses JSON: {resp_json}")

    if status_code != 200:
        print("[relay-e2e-raw] ERROR: /v1/responses did not return 200")
        return False

    try:
        outputs = resp_json["output"]
        first_item = outputs[0]
        text = first_item["content"][0]["text"]
    except Exception as exc:
        print(f"[relay-e2e-raw] ERROR: unexpected /v1/responses shape: {exc!r}")
        return False

    if text.strip() != "relay-http-ok":
        print(
            f"[relay-e2e-raw] ERROR: unexpected assistant text: {text!r} "
            "(wanted 'relay-http-ok')"
        )
        return False

    return True


def test_stream_responses() -> bool:
    print("=== 1b) /v1/responses (stream=true, SSE) ===")
    payload = {
        "model": "gpt-4o-mini",
        "input": "Say exactly: relay-stream-ok",
        "max_output_tokens": 64,
        "stream": True,
    }

    api_base = os.environ.get("API_BASE", REST_BASE + "/v1").rstrip("/")
    url = f"{api_base}/responses"

    session = requests.Session()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RELAY_KEY}",
    }

    if DEBUG:
        print(
            f"[relay-e2e-raw] [DEBUG] REQUEST POST /v1/responses (stream) "
            f"url={url}, json_body={payload}"
        )

    resp = session.post(url, json=payload, headers=headers, stream=True, timeout=60.0)
    print(
        f"[relay-e2e-raw] POST /v1/responses (stream) -> HTTP {resp.status_code}",
    )

    if resp.status_code != 200:
        print("[relay-e2e-raw] ERROR: streaming responses returned HTTP "
              f"{resp.status_code}")
        return False

    text_chunks: List[str] = []

    for event_type, data_str in _iter_sse_events(resp):
        try:
            obj = json.loads(data_str)
        except json.JSONDecodeError:
            if DEBUG:
                print(
                    "[relay-e2e-raw] [DEBUG] Failed to parse SSE data as JSON: "
                    f"{data_str!r}",
                )
            continue

        if event_type == "response.output_text.delta":
            delta = obj.get("delta", "")
            text_chunks.append(delta)

    aggregated_text = "".join(text_chunks).strip()
    print(
        f"[relay-e2e-raw] Streamed text aggregate: {aggregated_text!r}",
    )

    expected = "relay-stream-ok"
    if aggregated_text != expected:
        print(
            "[relay-e2e-raw] Unexpected streaming assistant text: "
            f"{aggregated_text!r} (wanted {expected!r})"
        )
        return False

    return True


def test_embeddings() -> bool:
    print("=== 2) /v1/embeddings ===")
    payload = {
        "model": "text-embedding-3-small",
        "input": ["hello", "world"],
    }
    status_code, resp_json = do_request("POST", "/v1/embeddings", payload)
    print(f"[relay-e2e-raw] POST /v1/embeddings -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /v1/embeddings JSON: keys={list(resp_json.keys())}")

    if status_code != 200:
        print("[relay-e2e-raw] ERROR: /v1/embeddings did not return 200")
        return False

    data = resp_json.get("data") or []
    if not data or "embedding" not in data[0]:
        print("[relay-e2e-raw] ERROR: /v1/embeddings missing embedding data")
        return False

    return True


def test_models() -> bool:
    print("=== 3) /v1/models ===")
    status_code, resp_json = do_request("GET", "/v1/models", None)
    print(f"[relay-e2e-raw] GET /v1/models -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /v1/models JSON: keys={list(resp_json.keys())}")

    if status_code != 200:
        print("[relay-e2e-raw] ERROR: /v1/models did not return 200")
        return False

    return True


def test_relay_models_best_effort() -> bool:
    print("=== 4) /relay/models (best-effort) ===")
    status_code, resp_json = do_request("GET", "/relay/models", None)
    print(f"[relay-e2e-raw] GET /relay/models -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /relay/models JSON: {resp_json}")
    # This is best-effort; 404 is acceptable depending on deployment.
    return True


def test_tools_best_effort() -> bool:
    print("=== 5) /v1/tools (best-effort) ===")
    status_code, resp_json = do_request("GET", "/v1/tools", None)
    print(f"[relay-e2e-raw] GET /v1/tools -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /v1/tools JSON: {resp_json}")
    # best-effort
    return True


def test_files_best_effort() -> bool:
    print("=== 6) /v1/files (best-effort) ===")
    status_code, resp_json = do_request("GET", "/v1/files", None)
    print(f"[relay-e2e-raw] GET /v1/files -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /v1/files JSON: {resp_json}")
    # best-effort
    return True


def test_vector_stores_best_effort() -> bool:
    print("=== 7) /v1/vector_stores (best-effort) ===")
    status_code, resp_json = do_request("GET", "/v1/vector_stores", None)
    print(f"[relay-e2e-raw] GET /v1/vector_stores -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /v1/vector_stores JSON: {resp_json}")
    # best-effort
    return True


def test_conversations_best_effort() -> bool:
    print("=== 8) /v1/conversations (best-effort) ===")
    payload = {
        "messages": [
            {"role": "user", "content": "Hello from relay-e2e-raw."},
        ]
    }
    status_code, resp_json = do_request("POST", "/v1/conversations", payload)
    print(f"[relay-e2e-raw] POST /v1/conversations -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /v1/conversations JSON: {resp_json}")
    # best-effort
    return True


def test_relay_actions_best_effort() -> bool:
    print("=== 9) /relay/actions (best-effort) ===")
    status_code, resp_json = do_request("GET", "/relay/actions", None)
    print(f"[relay-e2e-raw] GET /relay/actions -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /relay/actions JSON: {resp_json}")
    # best-effort
    return True


def test_realtime_sessions_best_effort() -> bool:
    print("=== 10) /v1/realtime/sessions (basic JSON, best-effort) ===")
    payload = {
        "model": "gpt-realtime-preview",
        "modalities": ["text"],
        "instructions": "You are a test assistant. Please echo a short greeting.",
        # IMPORTANT: do NOT include session_ttl_seconds; OpenAI 400s it.
    }
    status_code, resp_json = do_request("POST", "/v1/realtime/sessions", payload)
    print(f"[relay-e2e-raw] POST /v1/realtime/sessions -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /v1/realtime/sessions JSON: {resp_json}")
    # best-effort
    return True


def test_images_best_effort() -> bool:
    print("=== 11) /v1/images (direct, best-effort) ===")
    payload = {
        "model": "gpt-image-1",
        "prompt": "A simple icon of a red car on a white background.",
        "size": "512x512",
        "response_format": "b64_json",
    }
    status_code, resp_json = do_request("POST", "/v1/images", payload)
    print(f"[relay-e2e-raw] POST /v1/images -> HTTP {status_code}")
    print(
        "[relay-e2e-raw] /v1/images JSON (truncated keys): "
        f"{list(resp_json.keys())[:5]}"
    )
    # best-effort
    return True


def test_videos_best_effort() -> bool:
    print("=== 12) /v1/videos (direct, best-effort) ===")
    payload = {
        "model": "sora-2",
        "prompt": "Short 2 second test video of a red ball bouncing on a white floor.",
        # Per error message from upstream, 'seconds' must be one of
        # '4', '8', or '12' as a string, not integer.
        "seconds": "4",
        "size": "720x1280",
    }
    status_code, resp_json = do_request("POST", "/v1/videos", payload)
    print(f"[relay-e2e-raw] POST /v1/videos -> HTTP {status_code}")
    print(f"[relay-e2e-raw] /v1/videos JSON: {resp_json}")
    # best-effort
    return True


def main() -> int:
    ok_health = test_health()

    ok_non_stream = test_non_stream_responses()
    ok_stream = test_stream_responses()
    ok_embeddings = test_embeddings()
    ok_models = test_models()

    # Best-effort tests (do not gate the core "OK/FAIL" status)
    test_relay_models_best_effort()
    test_tools_best_effort()
    test_files_best_effort()
    test_vector_stores_best_effort()
    test_conversations_best_effort()
    test_relay_actions_best_effort()
    test_realtime_sessions_best_effort()
    test_images_best_effort()
    test_videos_best_effort()

    core_ok = ok_health and ok_non_stream and ok_stream and ok_embeddings and ok_models
    if core_ok:
        print("E2E RAW: CORE TESTS PASSED.")
        return 0
    else:
        print("E2E RAW: CORE TESTS FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
