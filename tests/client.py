# tests/client.py

import os
from starlette.testclient import TestClient

# Ensure the app sees a test-friendly environment *before* it is imported.
os.environ.setdefault("APP_MODE", "test")
os.environ.setdefault("ENVIRONMENT", "test")

# You explicitly chose Option A: disable relay auth in tests.
# This makes RelayAuthMiddleware's check_relay_key() a no-op.
os.environ.setdefault("RELAY_AUTH_ENABLED", "false")

# Upstream base URL can stay default; override if you proxy:
os.environ.setdefault("OPENAI_API_BASE", "https://api.openai.com/v1")

from app.main import app  # noqa: E402  (import after env is set)


def _build_client() -> TestClient:
    client = TestClient(app)

    # Optional: if you ever want to test auth-enabled paths locally,
    # set RELAY_KEY in your environment and this will send an Authorization header.
    relay_key = os.getenv("RELAY_KEY")
    if relay_key:
        client.headers.update({"Authorization": f"Bearer {relay_key}"})

    return client


# Shared client instance used by all tests via the fixture in conftest.py
client: TestClient = _build_client()
