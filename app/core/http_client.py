# app/core/http_client.py
from __future__ import annotations

import os
from typing import Dict, Optional

import httpx


# Defaults align with OpenAI REST API
_DEFAULT_OPENAI_BASE = "https://api.openai.com"


def get_openai_base_url() -> str:
    """
    Resolve the upstream OpenAI base URL from environment, with sensible defaults.

    Priority:
      1. OPENAI_API_BASE (full base URL, e.g. https://api.openai.com)
      2. OPENAI_BASE_URL
      3. Hard-coded default https://api.openai.com
    """
    base = (
        os.getenv("OPENAI_API_BASE")
        or os.getenv("OPENAI_BASE_URL")
        or _DEFAULT_OPENAI_BASE
    )
    return base.rstrip("/")  # avoid trailing slash issues


def get_openai_api_key() -> str:
    """
    Fetch OPENAI_API_KEY from environment.

    Relay should fail fast if this is missing in a real deployment.
    For tests you can either set it or monkeypatch this function.
    """
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        # For safety: keep this explicit so misconfig in prod is obvious.
        raise RuntimeError("OPENAI_API_KEY is not set in environment.")
    return key


def build_openai_headers(
    extra: Optional[Dict[str, str]] = None,
    *,
    beta: Optional[str] = None,
) -> Dict[str, str]:
    """
    Construct headers for calls to the OpenAI REST API.

    - Always sends Authorization + Content-Type.
    - Optionally sends OpenAI-Organization / OpenAI-Project.
    - Optionally sends OpenAI-Beta (e.g. 'responses=v1').
    """
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {get_openai_api_key()}",
        "Content-Type": "application/json",
    }

    org = os.getenv("OPENAI_ORG_ID") or os.getenv("OPENAI_ORGANIZATION")
    if org:
        headers["OpenAI-Organization"] = org

    project = os.getenv("OPENAI_PROJECT_ID")
    if project:
        headers["OpenAI-Project"] = project

    if beta:
        headers["OpenAI-Beta"] = beta

    if extra:
        headers.update(extra)

    return headers


def create_async_client(*, timeout: float = 600.0) -> httpx.AsyncClient:
    """
    Factory for the upstream HTTPX AsyncClient used by the relay.

    Keeping this in one place makes it trivial to monkeypatch in tests
    or adapt connection settings across the whole relay.
    """
    base_url = get_openai_base_url()
    return httpx.AsyncClient(base_url=base_url, timeout=timeout)
