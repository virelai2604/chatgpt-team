"""tests/conftest.py

Shared pytest fixtures.

We intentionally use `pytest_asyncio.fixture` (not `pytest.fixture`) because the repo
runs with `asyncio_mode = strict` (see pytest.ini). In strict mode, async fixtures
must be declared via pytest-asyncio, otherwise pytest will pass the async generator
object through to the test (leading to AttributeError crashes).
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator

import httpx
import pytest
import pytest_asyncio

from app.main import app


def _relay_token() -> str:
    # Prefer explicit RELAY_TOKEN, fall back to RELAY_KEY (pytest.ini sets RELAY_KEY by default).
    return os.getenv("RELAY_TOKEN") or os.getenv("RELAY_KEY") or "dummy"


def _auth_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    token = _relay_token()
    headers: dict[str, str] = {
        # Many deployments accept Authorization: Bearer <token>
        "Authorization": f"Bearer {token}",
        # Some deployments accept X-Relay-Key: <token>
        "X-Relay-Key": token,
    }
    if extra:
        headers.update(extra)
    return headers


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    # Keep anyio consistent; tests use httpx + ASGITransport and pytest-asyncio.
    return "asyncio"


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    """
    AsyncClient hitting the in-process ASGI app (no uvicorn required).
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers=_auth_headers(),
    ) as c:
        yield c


@pytest_asyncio.fixture
async def client(async_client: httpx.AsyncClient) -> AsyncIterator[httpx.AsyncClient]:
    """
    Backwards-compatible alias: some tests request 'client' instead of 'async_client'.
    """
    yield async_client
