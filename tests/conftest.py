# tests/conftest.py
from __future__ import annotations

import os
from typing import AsyncIterator

import httpx
import pytest
import pytest_asyncio

from app.main import app
from app.core.config import settings


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    """
    Shared async HTTP client that talks to the FastAPI app in-process via ASGI.

    - Uses httpx.ASGITransport so there is no real network involved.
    - Automatically sends Authorization: Bearer <RELAY_KEY or 'dummy'>,
      which matches how the OpenAI SDK talks to the relay in practice.
    """
    relay_key = os.getenv("RELAY_KEY", "dummy")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {relay_key}"},
        timeout=30.0,
    ) as client:
        yield client
