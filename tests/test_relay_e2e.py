# tests/test_relay_e2e.py

from __future__ import annotations

import os

import pytest

from relay_e2e_raw import main as relay_e2e_main


@pytest.mark.integration
def test_relay_e2e_raw_against_local_relay() -> None:
    """
    High-level E2E integration test.

    Preconditions:
      - Relay is running at REST_BASE (default http://127.0.0.1:8000)
      - RELAY_KEY is set in the environment and matches the relay config
      - OpenAI upstream credentials are configured in the relay's .env
    """

    # Ensure we have basic env vars for the E2E script
    if not os.getenv("RELAY_KEY"):
        pytest.skip("RELAY_KEY not set in environment")

    # Provide safe defaults if not overridden by CI/shell
    os.environ.setdefault("REST_BASE", "http://127.0.0.1:8000")
    os.environ.setdefault("TEST_MODEL", "gpt-5.1")
    os.environ.setdefault("EMBEDDING_MODEL", "text-embedding-3-small")
    os.environ.setdefault("IMAGE_MODEL", "gpt-image-1")
    os.environ.setdefault("REALTIME_MODEL", "gpt-4o-realtime-preview")

    # Run the raw script's main() – it raises on failure and returns 0 on success
    rc = relay_e2e_main()
    assert rc == 0
