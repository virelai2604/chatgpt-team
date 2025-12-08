from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app
from app.core import config


def _default_relay_key() -> str:
    """
    Use the configured relay key if present, otherwise a dummy test key.
    """
    key = getattr(config.settings, "RELAY_KEY", None)
    return key or "dummy-test-relay-key"


client = TestClient(
    app,
    headers={
        # Most tests don't care about auth details; this keeps them green even
        # when RELAY_AUTH_ENABLED is turned on.
        "Authorization": f"Bearer {_default_relay_key()}",
    },
)
