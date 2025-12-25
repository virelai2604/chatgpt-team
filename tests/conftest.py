import os

import httpx
import pytest


@pytest.fixture(scope="session")
def relay_base_url() -> str:
    return os.getenv("RELAY_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def relay_token() -> str:
    return os.getenv("RELAY_TOKEN", "")


@pytest.fixture(scope="session")
async def client(relay_base_url: str, relay_token: str):
    """
    Default integration client.

    Important: The test suite sets relay auth OFF by default so local tests run
    without requiring a key. Individual tests can monkeypatch settings to enable it.
    """
    os.environ.setdefault("RELAY_AUTH_ENABLED", "false")
    os.environ.setdefault("RELAY_KEY", "dummy")

    headers: dict[str, str] = {}
    if relay_token:
        headers["Authorization"] = f"Bearer {relay_token}"

    async with httpx.AsyncClient(
        base_url=relay_base_url,
        headers=headers,
        timeout=60.0,
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
async def async_client(client: httpx.AsyncClient) -> httpx.AsyncClient:
    """
    Alias fixture for tests that expect `async_client` by name.
    """
    return client
