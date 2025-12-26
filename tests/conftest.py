from __future__ import annotations

import os
from typing import Any, AsyncIterator, Dict, Optional

import httpx
import pytest
import pytest_asyncio

from app.main import app as fastapi_app


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v not in (None, "") else default


def _relay_base_url() -> str:
    return (_env("RELAY_BASE_URL", "http://localhost:8000") or "http://localhost:8000").rstrip("/")


def _relay_token() -> Optional[str]:
    # Prefer RELAY_TOKEN; fall back to RELAY_KEY for convenience.
    return _env("RELAY_TOKEN") or _env("RELAY_KEY")


def _auth_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Produce relay auth headers.

    We always send Authorization: Bearer <token> when a token is present.
    If RELAY_AUTH_HEADER is configured (e.g., x-relay-key), we ALSO send that header
    with the raw token value, to stay compatible with both auth styles.
    """
    headers: Dict[str, str] = {}
    token = _relay_token()

    if token:
        headers["Authorization"] = f"Bearer {token}"
        configured = _env("RELAY_AUTH_HEADER")
        if configured and configured.lower() not in ("authorization",):
            headers[configured] = token

    if extra:
        headers.update(extra)
    return headers


async def _probe_relay_or_skip(client: httpx.AsyncClient) -> None:
    """
    Make failures actionable:
      - Skip if relay is unreachable (forgot to start uvicorn, wrong base URL)
      - Skip if obviously missing token for Render (placeholder/dummy)
      - Otherwise continue and let tests assert behavior
    """
    base_url = _relay_base_url()
    token = _relay_token()

    # Common footgun: running against Render with RELAY_TOKEN unset or dummy
    if "onrender.com" in base_url and (not token or token.strip().lower() == "dummy"):
        pytest.skip(
            "RELAY_TOKEN is missing/placeholder while targeting Render. "
            "Export a real RELAY_TOKEN (and optionally RELAY_KEY) before running integration tests."
        )

    # Reachability probe (no hard dependency on auth-protected endpoints).
    try:
        r = await client.get("/v1/actions/ping")
    except Exception as e:
        pytest.skip(
            f"Relay not reachable at {base_url}. Start uvicorn locally or fix RELAY_BASE_URL. "
            f"Probe error: {type(e).__name__}: {e}"
        )

    # If ping itself is failing badly, skip.
    if r.status_code >= 500:
        pytest.skip(f"Relay is returning {r.status_code} for /v1/actions/ping; skipping integration tests.")


@pytest_asyncio.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """
    Live HTTP client for integration tests.

    These integration tests are intended to hit a running relay (localhost or Render),
    so they exercise the real middleware stack + upstream forwarding.
    """
    base_url = _relay_base_url()

    timeout = httpx.Timeout(
        connect=float(_env("HTTPX_CONNECT_TIMEOUT_S", "10")),
        read=float(_env("HTTPX_READ_TIMEOUT_S", "60")),
        write=float(_env("HTTPX_WRITE_TIMEOUT_S", "60")),
        pool=float(_env("HTTPX_POOL_TIMEOUT_S", "10")),
    )

    async with httpx.AsyncClient(
        base_url=base_url,
        headers=_auth_headers(),
        timeout=timeout,
        follow_redirects=True,
    ) as c:
        await _probe_relay_or_skip(c)
        yield c


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    """
    In-process ASGI client for local E2E tests.

    This does NOT require a running uvicorn server; it calls the FastAPI app directly.
    We still attach relay auth headers by default so /v1/* endpoints work when auth is enabled.
    """
    timeout = httpx.Timeout(
        connect=float(_env("HTTPX_CONNECT_TIMEOUT_S", "10")),
        read=float(_env("HTTPX_READ_TIMEOUT_S", "60")),
        write=float(_env("HTTPX_WRITE_TIMEOUT_S", "60")),
        pool=float(_env("HTTPX_POOL_TIMEOUT_S", "10")),
    )

    transport = httpx.ASGITransport(app=fastapi_app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers=_auth_headers(),
        timeout=timeout,
        follow_redirects=True,
    ) as c:
        yield c
