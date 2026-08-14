# tests/test_containers_file_content.py
"""GET /v1/containers/{container_id}/files/{file_id}/content.

Why this exists
---------------
This route had two defects, both invisible to the rest of the suite because no
test ever exercised it against an upstream:

1. The 2xx branch returned `StreamingResponse(upstream.aiter_bytes())` from
   *inside* `async with client.stream(...)`. The context manager closes the
   upstream response when the handler returns, which happens before Starlette
   iterates the body — so a successful download answered **200 with an empty
   body** while upstream had sent the file. A success status with no data is the
   worst possible failure mode: nothing downstream can tell it went wrong.

2. A transport failure (DNS, refused connection, timeout, a proxy rejecting
   CONNECT) raised out of `client.stream(...)` before any status code existed,
   escaping as a bare relay 500 — precisely what the handler's docstring says it
   exists to prevent. Every sibling route returns 424 for this.

Both are pinned here against a stub upstream, so neither can regress silently.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app

pytestmark = pytest.mark.unit

_PATH = "/v1/containers/cont_test/files/file_test/content"
_BODY = b"CONTAINER-FILE-CONTENT-" + b"x" * 200


@pytest.fixture(autouse=True)
def _no_relay_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """pytest-env sets RELAY_KEY, which flips auth on by default (config.py:343)."""
    monkeypatch.setattr(settings, "RELAY_AUTH_ENABLED", False, raising=False)


@pytest.fixture()
def stub_upstream() -> Iterator[str]:
    """A real HTTP server on a real socket.

    This cannot use httpx.MockTransport. MockTransport hands back an already
    buffered response, so `aiter_bytes()` keeps working after the response is
    closed and the close-before-iterate race simply does not occur — a
    MockTransport version of this test passes against the broken handler. Only a
    genuine streaming connection reproduces it.
    """

    class _H(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("content-type", "application/octet-stream")
            self.send_header("content-length", str(len(_BODY)))
            self.end_headers()
            self.wfile.write(_BODY)

        def log_message(self, *args: object) -> None:  # keep pytest output clean
            pass

    server = HTTPServer(("127.0.0.1", 0), _H)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


def test_successful_download_returns_the_body_not_an_empty_200(
    monkeypatch: pytest.MonkeyPatch, stub_upstream: str
) -> None:
    """The regression that mattered: 200 with zero bytes looks like success."""
    monkeypatch.setattr(settings, "OPENAI_API_BASE", stub_upstream, raising=False)
    monkeypatch.setattr(settings, "openai_base_url", stub_upstream, raising=False)

    with TestClient(create_app()) as client:
        r = client.get(_PATH)

    assert r.status_code == 200
    assert r.content == _BODY, (
        f"expected {len(_BODY)} bytes, got {len(r.content)} — the upstream response "
        "was closed before the streaming body could be read"
    )


def test_upstream_transport_failure_is_424_not_a_bare_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A dead upstream must degrade the same way every other route degrades."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("All connection attempts failed", request=request)

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        "app.routes.containers.get_async_httpx_client",
        lambda **kw: httpx.AsyncClient(transport=transport),
    )

    with TestClient(create_app(), raise_server_exceptions=False) as client:
        r = client.get(_PATH)

    assert r.status_code == 424, f"expected 424, got {r.status_code}: {r.text}"
    assert "Upstream request failed" in r.text


def test_upstream_error_status_is_propagated_verbatim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The handler must never mask an upstream 4xx behind a relay error."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"error": {"message": "No such file"}},
            headers={"content-type": "application/json"},
        )

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        "app.routes.containers.get_async_httpx_client",
        lambda **kw: httpx.AsyncClient(transport=transport),
    )

    with TestClient(create_app()) as client:
        r = client.get(_PATH)

    assert r.status_code == 404
    assert r.json()["error"]["message"] == "No such file"
