from __future__ import annotations

import os
import time
from collections import Counter
from typing import Any, Dict, Tuple

import httpx
import pytest


def _relay_base() -> str:
    return (os.environ.get("RELAY_BASE_URL") or os.environ.get("RELAY_BASE") or "http://localhost:8000").rstrip("/")


def _relay_token() -> str:
    return os.environ.get("RELAY_TOKEN") or os.environ.get("RELAY_KEY") or "dummy"


def _default_model() -> str:
    return os.environ.get("DEFAULT_MODEL") or "gpt-5.1"


def _headers(*, accept: str | None = None, content_type: str | None = None) -> Dict[str, str]:
    h = {"Authorization": f"Bearer {_relay_token()}"}
    if accept:
        h["Accept"] = accept
    if content_type:
        h["Content-Type"] = content_type
    return h


def _require_integration() -> None:
    if os.environ.get("INTEGRATION_OPENAI_API_KEY") not in {"1", "true", "TRUE", "yes", "YES"}:
        pytest.skip("Integration tests disabled (set INTEGRATION_OPENAI_API_KEY=1)")


def _skip_if_upstream_server_error(response: httpx.Response, *, label: str) -> None:
    if response.status_code < 500:
        return
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("type") == "server_error":
            message = error.get("message") or "Upstream server error."
            pytest.skip(f"{label}: {message}")
    assert response.status_code < 500, response.text


@pytest.mark.integration
def test_gate_a_uploads_e2e_happy_and_cancel() -> None:
    _require_integration()

    base = _relay_base()
    purpose = os.environ.get("UPLOAD_PURPOSE") or "batch"
    content = b"ping"
    filename = "upload_ping.txt"

    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            f"{base}/v1/uploads",
            headers=_headers(content_type="application/json"),
            json={"purpose": purpose, "filename": filename, "bytes": len(content), "mime_type": "text/plain"},
        )
        _skip_if_upstream_server_error(r, label="Upload create failed")
        assert r.status_code == 200, r.text
        upload_id = r.json().get("id")
        assert upload_id and isinstance(upload_id, str)

        files = {"data": (filename, content, "application/octet-stream")}
        r = client.post(f"{base}/v1/uploads/{upload_id}/parts", headers=_headers(), files=files)
        assert r.status_code == 200, r.text
        part_id = r.json().get("id")
        assert part_id and isinstance(part_id, str)

        r = client.post(
            f"{base}/v1/uploads/{upload_id}/complete",
            headers=_headers(content_type="application/json"),
            json={"part_ids": [part_id]},
        )
        _skip_if_upstream_server_error(r, label="Upload complete failed")
        assert r.status_code == 200, r.text
        completed = r.json()

        file_id = None
        if isinstance(completed.get("file"), dict):
            file_id = completed["file"].get("id")
        file_id = file_id or completed.get("file_id") or completed.get("file")
        assert file_id and isinstance(file_id, str), completed

        r = client.get(f"{base}/v1/files/{file_id}/content", headers=_headers())
        assert r.status_code == 200, r.text
        assert r.content == content

        r = client.post(
            f"{base}/v1/uploads",
            headers=_headers(content_type="application/json"),
            json={"purpose": purpose, "filename": "cancel_me.txt", "bytes": len(content), "mime_type": "text/plain"},
        )
        assert r.status_code == 200, r.text
        upload2_id = r.json().get("id")
        assert upload2_id and isinstance(upload2_id, str)

        r = client.post(f"{base}/v1/uploads/{upload2_id}/cancel", headers=_headers())
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "cancelled", r.text


@pytest.mark.integration
def test_gate_b_sse_smoke() -> None:
    _require_integration()

    base = _relay_base()
    model = _default_model()

    payload = {"model": model, "input": "Write exactly: 12345678901234567890"}
    max_seconds = float(os.environ.get("SSE_MAX_TIME_SECONDS") or "15")

    with httpx.Client(timeout=max_seconds + 10) as client:
        with client.stream(
            "POST",
            f"{base}/v1/responses:stream",
            headers=_headers(accept="text/event-stream", content_type="application/json"),
            json=payload,
        ) as r:
            assert r.status_code == 200, r.read().decode("utf-8", errors="replace")
            ctype = r.headers.get("content-type", "")
            assert "text/event-stream" in ctype.lower(), ctype

            saw_data = False
            buf = b""
            start = time.time()

            for chunk in r.iter_bytes():
                if chunk:
                    buf += chunk
                    if b"data:" in buf:
                        saw_data = True
                        break
                if time.time() - start > max_seconds:
                    break

            assert saw_data, buf[:800].decode("utf-8", errors="replace")


@pytest.mark.integration
def test_gate_c_openapi_operation_ids_unique() -> None:
    base = _relay_base()

    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{base}/openapi.json")
        assert r.status_code == 200, r.text
        spec = r.json()

    paths: Dict[str, Any] = spec.get("paths", {})
    op_ids: list[Tuple[str, str, str]] = []
    for path, ops in paths.items():
        if not isinstance(ops, dict):
            continue
        for method, meta in ops.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            if not isinstance(meta, dict):
                continue
            op_id = meta.get("operationId")
            if op_id:
                op_ids.append((op_id, method.upper(), path))

    counts = Counter([x[0] for x in op_ids])
    dupes = {k: v for k, v in counts.items() if v > 1}
    if dupes:
        lines = ["Duplicate operationId values detected:"]
        for op_id in sorted(dupes.keys()):
            lines.append(f"- {op_id}")
            for _, method, path in [x for x in op_ids if x[0] == op_id]:
                lines.append(f"    {method} {path}")
        raise AssertionError("\n".join(lines))


@pytest.mark.integration
def test_gate_d_content_endpoints_wiring_negative_ids() -> None:
    _require_integration()

    base = _relay_base()

    def check(url: str) -> None:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(url, headers=_headers())
            assert r.status_code != 500, r.text
            assert "application/json" in (r.headers.get("content-type") or "").lower(), r.headers
            body = r.json()
            assert isinstance(body, dict) and "error" in body and "message" in body["error"], body

    check(f"{base}/v1/containers/cont_invalid/files/file_invalid/content")
    check(f"{base}/v1/videos/video_invalid/content")
