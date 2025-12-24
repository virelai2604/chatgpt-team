from __future__ import annotations

import os

import pytest
import requests

RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
DEFAULT_TIMEOUT_S = float(os.getenv("DEFAULT_TIMEOUT_S", "20"))


def _auth_headers(extra: dict | None = None) -> dict:
    token = os.getenv("RELAY_TOKEN") or os.getenv("RELAY_KEY") or "dummy"
    headers = {"Authorization": f"Bearer {token}"}
    if extra:
        headers.update(extra)
    return headers


@pytest.mark.integration
def test_remaining_route_families_smoke_no_5xx() -> None:
    """
    Broad smoke coverage for remaining route families.
    Goal: wiring sanity (no relay 5xx), NOT functional correctness.
    """
    endpoints = [
        ("GET", "/v1/assistants", None),
        ("GET", "/v1/threads", None),
        ("GET", "/v1/runs", None),
        ("GET", "/v1/files", None),
        ("GET", "/v1/batches", None),
        ("GET", "/v1/fine_tuning/jobs", None),
        ("GET", "/v1/audio/models", None),
        ("GET", "/v1/organization/usage", None),
    ]

    for method, path, params in endpoints:
        r = requests.request(
            method,
            f"{RELAY_BASE_URL}{path}",
            headers=_auth_headers(),
            params=params,
            timeout=DEFAULT_TIMEOUT_S,
        )
        assert r.status_code < 500, f"{method} {path} returned {r.status_code}: {r.text[:400]}"
