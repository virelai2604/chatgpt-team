"""
Success gates for the relay (integration).

Gates:
- Gate A: Uploads E2E passes (happy path + cancel path)
- Gate B: SSE smoke passes (streaming content-type + incremental reads)
- Gate C: OpenAPI has no duplicate operationId warnings (validated by uniqueness check)
- Gate D: containers/videos `/content` endpoints validated (no relay 5xx; upstream 4xx is OK)

Requires:
  INTEGRATION_OPENAI_API_KEY=1
Optional env:
  RELAY_BASE_URL (default http://localhost:8000)
  RELAY_TOKEN    (default dummy)
  DEFAULT_MODEL  (default gpt-5.1)
"""

from __future__ import annotations

import os
from collections import Counter
from typing import Any, Dict, List

import pytest
import requests


pytestmark = pytest.mark.integration

RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
RELAY_TOKEN = os.getenv("RELAY_TOKEN", "dummy")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-5.1")

DEFAULT_TIMEOUT_S = float(os.getenv("RELAY_TEST_TIMEOUT_S", "60"))


def _skip_if_no_real_key() -> None:
    # Keep this consistent with existing integration tests.
    if os.getenv("INTEGRATION_OPENAI_API_KEY") != "1":
        pytest.skip("INTEGRATION_OPENAI_API_KEY != 1 (skipping real-API integration tests)")


def _auth_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    headers = {"Authorization": f"Bearer {RELAY_TOKEN}"}
    if extra:
        headers.update(extra)
    return headers


def _must_ok(r: requests.Response, *, hint: str = "") -> None:
    if r.ok:
        return
    # Provide debuggable payload (but keep it bounded).
    body = r.text
    if len(body) > 4000:
        body = body[:4000] + "…(truncated)"
    raise AssertionError(f"{hint}HTTP {r.status_code} {r.reason}: {body}")


# -------------------------
# Gate A: Uploads E2E
# -------------------------

def test_gate_a_uploads_e2e_happy_path_and_cancel_path() -> None:
    """
    Uploads API flow per OpenAI docs:
      1) POST /v1/uploads
      2) POST /v1/uploads/{upload_id}/parts (multipart field name: data)
      3) POST /v1/uploads/{upload_id}/complete (ordered part_ids)
      4) POST /v1/uploads/{upload_id}/cancel (cancel path)
    """
    _skip_if_no_real_key()

    # Happy path: upload a tiny file in a single part, then complete.
    payload = {
        "purpose": "batch",
        "filename": "relay_ping.txt",
        "bytes": 4,
        "mime_type": "text/plain",
        # expires_after optional; keep default behavior.
    }
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/uploads",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Create upload failed. ")
    upload = r.json()
    upload_id = upload.get("id")
    assert isinstance(upload_id, str) and upload_id.startswith("upload_")

    # Add one part (multipart, field name MUST be `data`).
    part_bytes = b"ping"
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/uploads/{upload_id}/parts",
        headers=_auth_headers(),
        files={"data": ("part.bin", part_bytes, "application/octet-stream")},
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Add upload part failed. ")
    part_obj = r.json()
    part_id = part_obj.get("id")
    assert isinstance(part_id, str) and part_id.startswith("part_")

    # Complete (md5 is optional per docs; omit to avoid format mismatch).
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/uploads/{upload_id}/complete",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={"part_ids": [part_id]},
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Complete upload failed. ")
    completed = r.json()
    assert completed.get("status") == "completed"
    file_obj = completed.get("file")
    assert isinstance(file_obj, dict)
    file_id = file_obj.get("id")
    assert isinstance(file_id, str) and file_id.startswith("file-")

    # Cancel path: create a second upload then cancel immediately.
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/uploads",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={
            "purpose": "batch",
            "filename": "relay_cancel.txt",
            "bytes": 1,
            "mime_type": "text/plain",
        },
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Create upload (cancel path) failed. ")
    cancel_upload_id = r.json().get("id")
    assert isinstance(cancel_upload_id, str) and cancel_upload_id.startswith("upload_")

    r = requests.post(
        f"{RELAY_BASE_URL}/v1/uploads/{cancel_upload_id}/cancel",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Cancel upload failed. ")
    cancelled = r.json()
    assert cancelled.get("status") == "cancelled"


# -------------------------
# Gate B: SSE smoke
# -------------------------

def test_gate_b_sse_smoke_streaming_content_type_and_incremental_reads() -> None:
    """
    Smoke-test the relay's SSE endpoint:
      - Content-Type includes text/event-stream
      - We receive multiple chunks/lines (incremental)
      - The streamed content contains the expected token ("pong")
    """
    _skip_if_no_real_key()

    with requests.post(
        f"{RELAY_BASE_URL}/v1/responses:stream",
        headers=_auth_headers(
            {
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            }
        ),
        json={"model": DEFAULT_MODEL, "input": "Return exactly: pong"},
        stream=True,
        timeout=DEFAULT_TIMEOUT_S,
    ) as r:
        _must_ok(r, hint="SSE request failed. ")
        ct = (r.headers.get("content-type") or "").lower()
        assert "text/event-stream" in ct

        lines: List[str] = []
        # Read up to N lines to avoid hanging if upstream stalls.
        for line in r.iter_lines(decode_unicode=True):
            if line is None:
                continue
            if line == "":
                continue
            lines.append(line)
            # Exit early once we see the expected token.
            if "pong" in line:
                break
            if len(lines) >= 200:
                break

        # Must have multiple lines to indicate incremental streaming.
        assert len(lines) >= 3, f"Expected multiple SSE lines, got {len(lines)} lines: {lines[:10]}"
        assert any("pong" in ln for ln in lines), f"Did not find 'pong' in SSE lines: {lines[:20]}"


# -------------------------
# Gate C: OpenAPI operationIds are unique
# -------------------------

def test_gate_c_openapi_has_no_duplicate_operation_ids() -> None:
    """
    FastAPI emits runtime warnings for duplicated operationIds.
    We validate the OpenAPI JSON that the relay serves has unique operationId values.
    """
    r = requests.get(f"{RELAY_BASE_URL}/openapi.json", timeout=DEFAULT_TIMEOUT_S)
    _must_ok(r, hint="GET /openapi.json failed. ")
    spec = r.json()

    op_ids: List[str] = []
    paths: Dict[str, Any] = spec.get("paths", {}) or {}
    for _path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for _method, op in methods.items():
            if not isinstance(op, dict):
                continue
            op_id = op.get("operationId")
            if isinstance(op_id, str) and op_id.strip():
                op_ids.append(op_id.strip())

    counts = Counter(op_ids)
    dups = sorted([op_id for op_id, n in counts.items() if n > 1])

    assert not dups, f"Duplicate operationId values found: {dups}"


# -------------------------
# Gate D: containers/videos content endpoints are wired
# -------------------------

def _assert_not_5xx(r: requests.Response, *, label: str) -> None:
    assert r.status_code < 500, f"{label} returned {r.status_code} (expected <500). Body: {r.text[:800]}"


def test_gate_d_containers_and_videos_content_endpoints_no_relay_5xx() -> None:
    """
    Without creating real container/video objects (cost/complexity),
    we validate that:
      - the endpoints exist and route to upstream
      - relay does not raise 5xx due to wiring/header bugs
    """
    # Containers file content (likely 404/400 from upstream due to dummy ids)
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/containers/cntr_dummy/files/file_dummy/content",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _assert_not_5xx(r, label="containers content")

    # Videos content (likely 404/400 from upstream due to dummy id)
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/videos/vid_dummy/content",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _assert_not_5xx(r, label="videos content")
