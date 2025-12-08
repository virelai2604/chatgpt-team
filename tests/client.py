# tests/client.py
import os

from starlette.testclient import TestClient

from app.main import app


def _build_client() -> TestClient:
    """
    Build a TestClient that matches the test environment defaults and
    automatically includes the relay Authorization header.
    """
    # Make sure these are set even if someone runs tests off‑CI
    os.environ.setdefault("APP_MODE", "test")
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("OPENAI_API_BASE", "https://api.openai.com/v1")

    client = TestClient(app)

    # Attach relay auth header if RELAY_KEY is configured (pytest.ini sets it)
    relay_key = os.getenv("RELAY_KEY")
    if relay_key:
        client.headers.update({"Authorization": f"Bearer {relay_key}"})

    return client


# Shared client instance for tests that import from tests.client
client: TestClient = _build_client()
