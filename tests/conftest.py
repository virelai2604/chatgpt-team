from __future__ import annotations

import httpx
import pytest_asyncio

from app.main import app as fastapi_app


@pytest_asyncio.fixture
async def async_client() -> httpx.AsyncClient:
    """
    Async HTTP client bound to the in-process FastAPI app.

    tests/test_local_e2e.py expects an `async_client` fixture.
    """
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def client(async_client: httpx.AsyncClient) -> httpx.AsyncClient:
    """
    Backwards-compatible alias. Some tests use `client`.
    """
    yield async_client
