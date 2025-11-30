# tests/test_health_and_tools.py
import os


def test_health_endpoint(client):
    # Relay health endpoint is exposed at /v1/health
    resp = client.get("/v1/health")
    assert resp.status_code == 200

    data = resp.json()
    assert data.get("object") == "health"
    assert data.get("status") == "ok"
    assert "environment" in data
    assert "default_model" in data


def test_tools_manifest_env_present():
    # We do not hit the filesystem here, only check that env is wired.
    assert os.getenv("TOOLS_MANIFEST"), "TOOLS_MANIFEST env var must be set"


def test_validation_schema_env_present():
    value = os.getenv("VALIDATION_SCHEMA_PATH")
    assert value is not None and value != ""
