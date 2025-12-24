from __future__ import annotations

import os
from typing import AsyncIterator, Dict

import httpx
import pytest_asyncio

from app.main import app


def _auth_header() -> Dict[str, str]:
    token = (os.getenv("RELAY_KEY") or os.getenv("RELAY_TOKEN") or "").strip()
    return {"Authorization": f"Bearer {token}"} if token else {}


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    """
    In-process client for local relay tests that use ASGITransport (no uvicorn needed).
    """
    base_url = os.getenv("RELAY_TEST_BASE_URL", "http://testserver")
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    async with httpx.AsyncClient(
        transport=transport,
        base_url=base_url,
        headers=_auth_header() or None,
    ) as c:
        yield c


@pytest_asyncio.fixture
async def client(async_client: httpx.AsyncClient) -> httpx.AsyncClient:
    """
    Backwards-compatible alias used by some tests.
    """
    return async_client
