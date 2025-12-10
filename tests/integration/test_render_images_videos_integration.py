# tests/test_render_images_videos_integration.py

import os
import typing as t

import pytest
import requests


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("RENDER_RELAY_BASE_URL")
if not BASE_URL:
    # You can set a sensible default here if you like, e.g.:
    # BASE_URL = "https://chatgpt-team-relay.onrender.com"
    pytest.skip(
        "RENDER_RELAY_BASE_URL is not set; skipping Render integration tests.",
        allow_module_level=True,
    )

# Prefer a dedicated client key if you have one; fall back to RELAY_KEY.
RENDER_RELAY_KEY = (
    os.environ.get("RENDER_RELAY_KEY") or os.environ.get("RELAY_KEY") or ""
)


def _build_url(path: str) -> str:
    path = path.lstrip("/")
    return f"{BASE_URL.rstrip('/')}/{path}"


def _auth_headers() -> dict:
    headers: dict = {}
    if RENDER_RELAY_KEY:
        headers["Authorization"] = f"Bearer {RENDER_RELAY_KEY}"
    return headers


def _request(
    method: str,
    path: str,
    *,
    timeout: int = 60,
    **kwargs: t.Any,
) -> requests.Response:
    """
    Small helper that:
      - injects Authorization if we have a relay key
      - fails fast if we accidentally get HTML instead of JSON/binary
    """
    url = _build_url(path)
    headers = kwargs.pop("headers", {})
    headers.update(_auth_headers())

    resp = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)

    # If we get HTML here, something is misconfigured (Cloudflare, 400 HTML, etc.)
    ct = resp.headers.get("content-type", "")
    if "text/html" in ct:
        # Show a small slice of the body for debugging
        snippet = resp.text[:200].replace("\n", " ")
        pytest.fail(f"Unexpected HTML from {url}: {resp.status_code} {snippet}")

    return resp


def _json_or_skip(resp: requests.Response) -> dict:
    """
    Try to decode JSON. If that fails, treat this as a hard failure.
    """
 try:
    data = resp.json()
except ValueError as exc:
    raise AssertionError(
        f"Expected JSON but got: {resp.status_code} {resp.text[:200]!r}"
    ) from exc


# ---------------------------------------------------------------------------
# Basic health check
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.render
def test_render_health_ok() -> None:
    """
    Sanity check: /v1/health on the Render relay.
    This should always be 200 if the service is up.
    """
    resp = _request("GET", "/v1/health")
    assert resp.status_code == 200, resp.text

    data = _json_or_skip(resp)
    # Be permissive: just check a couple of keys that should always be there.
    assert "relay" in data
    assert "meta" in data


# ---------------------------------------------------------------------------
# Image generations
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.render
def test_render_image_generations_smoke() -> None:
    """
    Hit POST /v1/images/generations on the Render relay.

    We are intentionally permissive:
      - If the account doesn't have access to gpt-image-1 or image gen,
        and OpenAI returns a structured error (4xx), we SKIP.
      - Only 5xx / transport-level issues count as failures.
    """
    payload = {
        "model": "gpt-image-1",
        "prompt": "A very small test image of a relay server icon",
        "size": "512x512",
    }

    resp = _request("POST", "/v1/images/generations", json=payload)

    # Hard failures: relay / upstream is actually broken.
    if resp.status_code >= 500:
        pytest.fail(f"Server error from images/generations: {resp.status_code} {resp.text[:200]}")

    data = _json_or_skip(resp)

    # If we don't get 200, assume it's a feature-gating / model access issue.
    if resp.status_code != 200:
        pytest.skip(
            f"Image generations not usable in this environment "
            f"(status={resp.status_code}, error={data.get('error')})"
        )

    # Minimal shape check for a successful response
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1


# ---------------------------------------------------------------------------
# Video generations
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.render
def test_render_video_generations_smoke() -> None:
    """
    Hit POST /v1/videos/generations on the Render relay.

    Same philosophy as images:
      - Treat well-formed 4xx as gating and SKIP.
      - Only treat 5xx / non-JSON as failure.
    """
    payload = {
        "model": "gpt-video-1",
        "prompt": "A tiny test animation of a relay server pulsing",
        "duration": 3,
    }

    resp = _request("POST", "/v1/videos/generations", json=payload, timeout=120)

    if resp.status_code >= 500:
        pytest.fail(f"Server error from videos/generations: {resp.status_code} {resp.text[:200]}")

    data = _json_or_skip(resp)

    if resp.status_code != 200:
        pytest.skip(
            f"Video generations not usable in this environment "
            f"(status={resp.status_code}, error={data.get('error')})"
        )

    # The exact schema is still evolving; just check for an id + object.
    assert "id" in data
    assert data.get("object") in {"video", "video.job", "video_generation"}  # be forgiving
