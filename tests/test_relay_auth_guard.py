# tests/test_relay_auth_guard.py
from __future__ import annotations

import os

import httpx
import pytest

from app.main import app

# All tests here are async
pytestmark = pytest.mark.asyncio


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RELAY_AUTH_ENABLED", "false").lower() != "true",
    reason="Set RELAY_AUTH_ENABLED=true to run auth guard test",
)
async def test_responses_requires_valid_relay_key() -> None:
    """
    When RELAY_AUTH_ENABLED=true and no relay key is provided, the relay
    must reject the request with 401/403 rather than silently forwarding.
    """
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        timeout=30.0,
    ) as client:
        # No Authorization, no X-Relay-Key
        resp = await client.post(
            "/v1/responses",
            json={"model": "gpt-5.1", "input": "Should not succeed"},
        )

    assert resp.status_code in (401, 403)
