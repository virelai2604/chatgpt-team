# tests/conftest.py

import os

import httpx
import pytest
from httpx import ASGITransport

# IMPORTANT:
# Ensure auth is disabled for in-process ASGITransport tests unless the runner
# explicitly enables it. This must happen before importing app.main.
os.environ.setdefault("RELAY_AUTH_ENABLED", "false")

from app.main import app  # noqa: E402  (import after env var set is intentional)

BASE_URL = os.environ.get("RELAY_TEST_BASE_URL", "http://testserver")


@pytest.fixture
async def async_client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE_URL,
        timeout=30.0,
    ) as client:
        yield client
