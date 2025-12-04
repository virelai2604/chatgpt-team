from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Tuple

import httpx
import pytest
from starlette.testclient import TestClient

from app.main import app


# ---------------------------------------------------------------------------
# Base async backend for pytest-anyio
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Ensure async tests run with asyncio backend.
    """
    return "asyncio"


# ---------------------------------------------------------------------------
# Shared TestClient for tests
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """
    Starlette TestClient bound to our FastAPI app.

    Ensures APP_MODE/ENVIRONMENT defaults for test runs.
    """
    os.environ.setdefault("APP_MODE", "test")
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("OPENAI_API_BASE", "https://api.openai.com")
    os.environ.setdefault("DEFAULT_MODEL", "gpt-4o-mini")
    return TestClient(app)


# ---------------------------------------------------------------------------
# Spy object for orchestrator / forwarding tests
# ---------------------------------------------------------------------------


@pytest.fixture
def forward_spy() -> Dict[str, Any]:
    """
    Mutable dict capturing "upstream" call details when FakeAsyncClient is used.
    """
    return {
        "called": False,
        "method": None,
        "url": None,
        "path": None,
        "subpath": None,
        "body": "",
        "json": None,
    }


# ---------------------------------------------------------------------------
# OpenAI stub payloads
# ---------------------------------------------------------------------------


def _echo_payload(path: str, method: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic echo payload used by most stubbed /v1 routes.

    Tests typically assert:
      - object == "test_proxy"
      - echo_path == <expected path>
      - echo_method == <expected method>
      - forward_spy["json"] == payload  (for POSTs with JSON bodies)
    """
    return {
        "object": "test_proxy",
        "echo_path": path,
        "echo_method": method,
        "echo_json": body,
    }


def _build_openai_stub_response(
    path: str,
    method: str,
    json_body: Any,
) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
    """
    Build a fake OpenAI-style response for the given path/method/body.

    IMPORTANT:
    - Never returns None.
    - Always returns (status_code, payload, headers).
    - Provides explicit stubs for the endpoints used by "pure local" tests,
      plus a safe generic fallback for any other /v1/* path.
    """
    method = method.upper()

    if json_body is None:
        body: Dict[str, Any] = {}
    elif isinstance(json_body, dict):
        body = json_body
    else:
        # If the body is not a dict (e.g. list or string), wrap it.
        body = {"data": json_body}

    headers: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # 1) Endpoints that tests expect to return a "test_proxy" echo payload
    # ------------------------------------------------------------------
    proxy_echo_paths = {
        # embeddings / images / videos (basic forward tests)
        "/v1/embeddings",
        "/v1/images/generations",
        "/v1/videos/generations",
        # files
        "/v1/files",
        # models
        "/v1/models",
        # realtime
        "/v1/realtime/sessions",
    }

    if path in proxy_echo_paths:
        return 200, _echo_payload(path, method, body), headers

    # Files detail / content
    if path.startswith("/v1/files/"):
        # All file detail/content operations in tests only check
        # echo_* fields.
        return 200, _echo_payload(path, method, body), headers

    # Vector store routes
    if path == "/v1/vector_stores" or path.startswith("/v1/vector_stores/"):
        return 200, _echo_payload(path, method, body), headers

    # Model detail routes
    if path.startswith("/v1/models/"):
        # For pure-local tests we treat this as a proxy echo as well.
        return 200, _echo_payload(path, method, body), headers

    # Responses API (proxy-style tests)
    if path == "/v1/responses":
        # create + list (POST/GET) – tests only assert on echo_* + spy
        return 200, _echo_payload(path, method, body), headers

    if path.startswith("/v1/responses/"):
        # single response + cancel – echo only
        return 200, _echo_payload(path, method, body), headers

    # Conversations API (your local store; tests still treat as proxy echo)
    if path == "/v1/conversations" or path.startswith("/v1/conversations/"):
        return 200, _echo_payload(path, method, body), headers

    # ------------------------------------------------------------------
    # 2) Audio special-case used by orchestrator "unknown path" test
    # ------------------------------------------------------------------
    if path.startswith("/v1/audio/speech") and method == "POST":
        # Test only cares about status_code in (200, 404) and that the JSON
        # body was forwarded; we keep the response simple.
        payload = _echo_payload(path, method, body)
        return 404, payload, headers

    # ------------------------------------------------------------------
    # 3) Generic fallback for any other /v1/* path
    # ------------------------------------------------------------------
    if path.startswith("/v1/"):
        payload = _echo_payload(path, method, body)
        return 200, payload, headers

    # ------------------------------------------------------------------
    # 4) Non-/v1 paths – minimal OK JSON
    # ------------------------------------------------------------------
    payload = _echo_payload(path, method, body)
    return 200, payload, headers


# ---------------------------------------------------------------------------
# Autouse patch: httpx.AsyncClient → FakeAsyncClient
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def patch_httpx_async_client(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    forward_spy: Dict[str, Any],
) -> None:
    """
    For tests that do NOT use httpx_mock, stub all upstream OpenAI calls.

    For tests that *do* use httpx_mock (e.g. test_routes_forwarding_smoke),
    we leave httpx.AsyncClient alone so pytest_httpx can intercept the real
    HTTP layer and count calls correctly.

    Additionally, when the 'requests_mock' fixture is present (used by
    tests/test_images_and_videos_routes_extra.py), we provide more
    realistic OpenAI-style stubs for the specific endpoints those tests
    exercise (images edits, video metadata/content, delete error paths).
    """
    # If this test uses the pytest_httpx fixture, do not patch.
    if "httpx_mock" in request.fixturenames:
        yield
        return

    # Extra upstream-like stubs are needed for the images/videos extra tests.
    use_extra_stubs = "requests_mock" in request.fixturenames

    class FakeAsyncClient:
        def __init__(
            self,
            *args: Any,
            base_url: Optional[str] = None,
            **kwargs: Any,
        ) -> None:
            self._base_url = str(base_url) if base_url is not None else ""

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
            # Compose full URL if base_url is set and url is relative
            if self._base_url and not (
                url.startswith("http://") or url.startswith("https://")
            ):
                full_url = self._base_url.rstrip("/") + "/" + url.lstrip("/")
            else:
                full_url = url

            parsed = httpx.URL(full_url)
            path = parsed.path
            method_upper = method.upper()

            json_body = kwargs.get("json")
            body_content = kwargs.get("content", b"")

            if isinstance(body_content, bytes):
                body_text = body_content.decode("utf-8", "ignore")
            else:
                body_text = str(body_content or "")

            # If no explicit json= was passed, but content looks like JSON, parse it.
            if json_body is None:
                text = body_text.lstrip()
                if text.startswith("{") or text.startswith("["):
                    try:
                        json_body = json.loads(text)
                    except Exception:
                        json_body = None

            # Fill spy for orchestrator tests
            forward_spy["called"] = True
            forward_spy["method"] = method_upper
            forward_spy["url"] = full_url
            forward_spy["path"] = path
            if path.startswith("/v1/videos/"):
                forward_spy["subpath"] = path.split("/v1/videos/")[-1]
            else:
                forward_spy["subpath"] = None
            forward_spy["body"] = body_text
            forward_spy["json"] = json_body

            # ------------------------------------------------------------------
            # Extra stubs for tests/test_images_and_videos_routes_extra.py
            # These tests use the `requests_mock` fixture, which we detect
            # via `use_extra_stubs`, and expect realistic OpenAI responses.
            # ------------------------------------------------------------------
            if use_extra_stubs:
                # POST /v1/images/edits → JSON image edit response
                if path == "/v1/images/edits" and method_upper == "POST":
                    payload = {
                        "created": 1234567890,
                        "data": [
                            {
                                "url": "https://example.test/generated-image.png",
                            }
                        ],
                    }
                    return httpx.Response(status_code=200, json=payload)

                # GET /v1/videos/video_123 → video metadata
                if path == "/v1/videos/video_123" and method_upper == "GET":
                    payload = {
                        "id": "video_123",
                        "object": "video",
                        "status": "completed",
                        "duration": 8,
                        "model": "sora-1",
                    }
                    return httpx.Response(status_code=200, json=payload)

                # GET /v1/videos/video_123/content → binary MP4 bytes
                if path == "/v1/videos/video_123/content" and method_upper == "GET":
                    # Simulate the same tiny MP4 payload as the test
                    video_bytes = b"\x00\x00\x00\x14ftypmp42"
                    headers = {"content-type": "video/mp4"}
                    return httpx.Response(
                        status_code=200,
                        content=video_bytes,
                        headers=headers,
                    )

                # DELETE /v1/videos/video_404 → 404 error passthrough
                if path == "/v1/videos/video_404" and method_upper == "DELETE":
                    payload = {
                        "error": {
                            "message": "Video 'video_404' not found",
                            "type": "invalid_request_error",
                        }
                    }
                    return httpx.Response(status_code=404, json=payload)

                # DELETE /v1/models/bad-model → 404 error passthrough
                if path == "/v1/models/bad-model" and method_upper == "DELETE":
                    payload = {
                        "error": {
                            "message": "Model 'bad-model' does not exist",
                            "type": "invalid_request_error",
                        }
                    }
                    return httpx.Response(status_code=404, json=payload)

            # ------------------------------------------------------------------
            # Default stub behavior for all other calls
            # ------------------------------------------------------------------
            status_code, payload, headers = _build_openai_stub_response(
                path, method_upper, json_body
            )
            return httpx.Response(status_code=status_code, json=payload, headers=headers)

        async def get(self, url: str, **kwargs: Any) -> httpx.Response:
            return await self.request("GET", url, **kwargs)

        async def post(self, url: str, **kwargs: Any) -> httpx.Response:
            return await self.request("POST", url, **kwargs)

        async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
            return await self.request("DELETE", url, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    yield
