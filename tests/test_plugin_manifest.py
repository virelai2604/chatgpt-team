# tests/test_plugin_manifest.py
"""Plugin/Actions discovery surface.

Why this exists
---------------
`static/.well-known/ai-plugin.json` drifted badly while nobody was looking: it
advertised `"auth": {"type": "none"}` against a relay that requires a key, pointed
`api.url` at `/openapi.yaml` (404), pointed `logo_url` at a file that does not
exist, and told models to use `/v1/tools` (404). The file itself was unreachable
because `static/` was never mounted, so none of it was observable.

These tests pin the discovery surface: served, parseable, honest about auth, and
pointing only at endpoints that actually answer.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app, create_app

pytestmark = pytest.mark.unit

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "static" / ".well-known" / "ai-plugin.json"


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_is_served_without_a_relay_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Discovery must work before a client has credentials."""
    monkeypatch.setattr(settings, "RELAY_AUTH_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "RELAY_KEY", "unit-test-key", raising=False)

    with TestClient(create_app()) as client:
        r = client.get("/.well-known/ai-plugin.json")
        assert r.status_code == 200, "plugin manifest must be reachable anonymously"
        assert r.json()["schema_version"] == "v1"

        # ...but the API itself stays gated.
        assert client.get("/v1/models").status_code == 401


def test_manifest_declares_the_auth_the_relay_actually_enforces() -> None:
    """`"type": "none"` here while the relay returns 401 is a silent integration break."""
    auth = _manifest()["auth"]
    assert auth["type"] != "none", "relay requires a key; manifest must not advertise open access"
    assert auth["authorization_type"] == "bearer"
    assert _manifest()["api"]["has_user_authentication"] is True


def test_manifest_only_points_at_endpoints_that_exist() -> None:
    """Every path the manifest names must answer, so clients and models aren't sent to 404s."""
    m = _manifest()

    with TestClient(app) as client:
        # The OpenAPI document the manifest advertises.
        api_path = "/" + m["api"]["url"].split("/", 3)[3]
        assert client.get(api_path).status_code == 200, f"api.url points at {api_path}, which 404s"

        # Every /v1/... path named in the model-facing description must exist.
        advertised = set(re.findall(r"/v1/[a-z0-9/_-]+", m["description_for_model"]))
        assert advertised, "description_for_model names no endpoints — did it get emptied?"
        for path in sorted(advertised):
            # 405 == route exists but is POST-only, which is fine here.
            assert client.get(path).status_code != 404, f"{path} is advertised to models but 404s"

    # A logo_url must not be declared unless the asset is actually present.
    if "logo_url" in m:
        logo = MANIFEST_PATH.parent.parent / m["logo_url"].rsplit("/static/", 1)[-1]
        assert logo.is_file(), "logo_url is declared but the file does not exist"


def test_manifest_has_no_placeholder_urls() -> None:
    """example.com placeholders shipped in this file for months."""
    raw = MANIFEST_PATH.read_text(encoding="utf-8")
    assert "example.com" not in raw


def test_actions_schema_declares_a_server() -> None:
    """ChatGPT Actions cannot dispatch a request without `servers`.

    FastAPI emits none, and the Actions subset shipped without one — so the schema
    ai-plugin.json points clients at could not actually be called.
    """
    with TestClient(app, base_url="https://ai.lafiel.me") as client:
        doc = client.get("/openapi.actions.json").json()

    servers = doc.get("servers") or []
    assert servers, "Actions subset must declare a server or the schema is uncallable"
    # Derived from the request, so it is correct on whichever domain served it.
    assert servers[0]["url"] == "https://ai.lafiel.me"


def test_actions_schema_advertises_only_real_paths() -> None:
    """A curated subset must not outlive the routes it curates."""
    with TestClient(app) as client:
        doc = client.get("/openapi.actions.json").json()

    live = set(app.openapi().get("paths", {}))
    phantom = sorted(set(doc.get("paths", {})) - live)
    assert not phantom, f"Actions schema advertises paths the app does not serve: {phantom}"
    assert doc["paths"], "Actions subset is empty — the curation filter matched nothing"
