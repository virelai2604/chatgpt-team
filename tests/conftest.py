# tests/conftest.py
from __future__ import annotations

import os

import httpx
import pytest_asyncio

from app.main import app

BASE_URL = os.environ.get("RELAY_TEST_BASE_URL", "http://testserver")


@pytest_asyncio.fixture
async def async_client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as client:
        yield client


# Backward-compatible alias for test modules that use `client`
@pytest_asyncio.fixture
async def client(async_client: httpx.AsyncClient) -> httpx.AsyncClient:
    return async_client
