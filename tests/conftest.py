# tests/conftest.py
import json
import os
from typing import Any, Dict, Optional

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app as fastapi_app

# Re-use the shared client logic from tests/client.py so the Authorization
# header is always correct for the relay.
from .client import client as shared_client  # noqa: F401


# --- OpenAI HTTP stub -----------------------------------------------------


class FakeResponse:
    def __init__(self, status_code: int = 200, json_data: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self) -> Dict[str, Any]:
        return self._json_data


class FakeAsyncClient:
    """
    Minimal httpx.AsyncClient stub that pretends to be the OpenAI backend.

    We only implement what forward_openai uses: .post()/.get() returning
    an object with .json().
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        self.base_url = kwargs.get("base_url")

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, url: str, *args: Any, **kwargs: Any) -> FakeResponse:
        return _build_openai_stub_response("GET", url, kwargs.get("json"))

    async def post(self, url: str, *args: Any, **kwargs: Any) -> FakeResponse:
        return _build_openai_stub_response("POST", url, kwargs.get("json"))


def _build_openai_stub_response(method: str, url: str, body: Optional[Dict[str, Any]]) -> FakeResponse:
    """
    Return a small, deterministic payload that looks like the real OpenAI API
    but is fast and completely local.
    """
    # Normalise path (strip any host prefix)
    if "://" in url:
        path = url.split("://", 1)[1]
        path = path[path.find("/") :]
    else:
        path = url

    # Models
    if path.startswith("/v1/models"):
        return FakeResponse(
            200,
            {
                "object": "list",
                "data": [
                    {"id": "gpt-4o-mini", "object": "model"},
                    {"id": "gpt-4.1-mini", "object": "model"},
                ],
            },
        )

    # Embeddings
    if path.startswith("/v1/embeddings"):
        return FakeResponse(
            200,
            {
                "object": "list",
                "data": [
                    {
                        "object": "embedding",
                        "index": 0,
                        "embedding": [0.1, 0.2, 0.3],
                    }
                ],
            },
        )

    # Responses (chat-style)
    if path.startswith("/v1/responses"):
        return FakeResponse(
            200,
            {
                "id": "resp_test",
                "object": "response",
                "model": (body or {}).get("model", "gpt-4o-mini"),
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {"type": "output_text", "text": "stubbed response from FakeAsyncClient"}
                        ],
                    }
                ],
            },
        )

    # Images
    if path.startswith("/v1/images"):
        return FakeResponse(
            200,
            {
                "created": 1234567890,
                "data": [{"b64_json": "fake-base64-image"}],
            },
        )

    # Videos (if you wire /v1/videos/generations through)
    if path.startswith("/v1/videos"):
        return FakeResponse(
            200,
            {
                "created": 1234567890,
                "data": [{"id": "video_123", "status": "completed"}],
            },
        )

    # Files
    if path.startswith("/v1/files"):
        return FakeResponse(
            200,
            {
                "object": "list",
                "data": [
                    {
                        "id": "file_test",
                        "object": "file",
                        "filename": "relay-e2e.txt",
                        "bytes": 10,
                    }
                ],
            },
        )

    # Vector stores
    if path.startswith("/v1/vector_stores"):
        return FakeResponse(
            200,
            {
                "object": "list",
                "data": [
                    {"id": "vs_test", "object": "vector_store", "name": "stub-store"},
                ],
            },
        )

    # Fallback: just echo what we got, so tests can inspect it
    return FakeResponse(
        200,
        {
            "method": method,
            "path": path,
            "body": body or {},
        },
    )


@pytest.fixture
def forward_spy(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    """
    Fixture that lets tests inspect which URL/body the relay tried to send
    to OpenAI via httpx.AsyncClient.
    """
    calls: Dict[str, Any] = {}

    original_async_client = httpx.AsyncClient

    def _make_fake_client(*args: Any, **kwargs: Any) -> FakeAsyncClient:
        calls["last_args"] = args
        calls["last_kwargs"] = kwargs
        return FakeAsyncClient(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _make_fake_client)

    yield calls

    # Restore for safety (not strictly necessary in tests, but harmless)
    httpx.AsyncClient = original_async_client  # type: ignore[assignment]


# --- FastAPI TestClient fixture -------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """
    Main TestClient fixture used by most tests.

    - Ensures ENVIRONMENT/APP_MODE defaults.
    - Reuses the shared client from tests/client.py so that:
      * Authorization: Bearer <RELAY_KEY> is always attached.
      * Relay auth (authy.check_relay_key) passes by default.
    """
    os.environ.setdefault("APP_MODE", "test")
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("OPENAI_API_BASE", "https://api.openai.com/v1")
    os.environ.setdefault("DEFAULT_MODEL", "gpt-4o-mini")

    # The shared_client already wraps the imported FastAPI app.
    return shared_client  # type: ignore[return-value]
