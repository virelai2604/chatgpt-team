# tests/test_upstream_path_rewrites.py
"""Relay aliases must be rewritten to paths OpenAI actually serves.

Why this exists
---------------
`forward_openai_request()` preserves the inbound path by default
(`upstream_path_final = upstream_path or request.url.path`). That is correct for
a transparent proxy, but it means any route the relay serves under a name OpenAI
does *not* serve is forwarded verbatim and can only 404 upstream.

`POST /v1/images` was exactly that. OpenAI's spec declares `/v1/images/generations`,
`/v1/images/edits` and `/v1/images/variations` -- there is no bare `/v1/images`.
Checked against `api_reference/openapi.transformed.yml` from openai/openai-python
at v3.1.0 (`10ee3f0d`). `/v1/videos/generations` had already been given an explicit
rewrite; `/v1/images` had not, and shared a handler with `/images/generations`.

These tests pin the rewrite target for both aliases, so an alias cannot silently
regress to forwarding its own path.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app

pytestmark = pytest.mark.unit

# alias path -> the upstream path it must be rewritten to
REWRITES = {
    "/v1/images": "/v1/images/generations",
    "/v1/videos/generations": "/v1/videos",
}


@pytest.fixture
def captured(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record the upstream path each alias forwards to, without any network."""
    seen: list[str] = []

    async def fake_forward(request, *, upstream_path=None, method=None, query=None):
        from fastapi.responses import JSONResponse

        seen.append(upstream_path or request.url.path)
        return JSONResponse({"ok": True})

    # Patch at each call site: the routers imported the symbol by name.
    import app.routes.images as images_mod
    import app.routes.videos as videos_mod

    monkeypatch.setattr(images_mod, "forward_openai_request", fake_forward)
    monkeypatch.setattr(videos_mod, "forward_openai_method_path", _method_path_shim(seen))
    return seen


def _method_path_shim(seen: list[str]):
    async def fake(method, path, **kwargs):
        from fastapi.responses import JSONResponse

        seen.append(path)
        return JSONResponse({"ok": True})

    return fake


@pytest.mark.parametrize(("alias", "expected"), sorted(REWRITES.items()))
def test_alias_is_rewritten_to_a_path_openai_serves(
    alias: str, expected: str, captured: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Auth off, or RelayAuthMiddleware answers 401 before routing and the
    # assertion below passes without a handler ever running.
    monkeypatch.setattr(settings, "RELAY_AUTH_ENABLED", False, raising=False)

    with TestClient(create_app()) as client:
        r = client.post(alias, json={"prompt": "ping", "model": "__invalid_model__"})

    assert r.status_code != 401, (
        f"{alias} returned 401 -- auth is on, so the handler never ran and this "
        "check cannot see the rewrite."
    )
    assert captured, f"{alias} did not reach a forwarding call at all (status {r.status_code})"
    assert captured[-1] == expected, (
        f"{alias} forwards to {captured[-1]!r}, but OpenAI serves {expected!r}. "
        "Forwarding the alias path verbatim can only 404 upstream."
    )
