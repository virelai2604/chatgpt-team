from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from starlette.datastructures import Headers


def _norm_header_name(name: str) -> str:
    return (name or "").strip().lower()


def get_auth_header_key(settings) -> str:
    """
    Returns the configured relay auth header name (normalized).
    Defaults to 'x-relay-key'.
    """
    raw = getattr(settings, "RELAY_AUTH_HEADER", None) or getattr(settings, "relay_auth_header", None) or "x-relay-key"
    return _norm_header_name(raw)


def _get_expected_key(settings) -> str:
    return getattr(settings, "RELAY_KEY", None) or getattr(settings, "relay_key", None) or ""


def check_relay_key(headers: Headers, settings) -> None:
    """
    Enforces relay auth when enabled.

    Semantics (aligned to tests):
    - If Authorization is present but not Bearer => 401 detail includes 'Bearer'
    - If missing => 401 'Missing relay key'
    - If provided but wrong => 401 'Invalid relay key'
    """
    enabled = bool(getattr(settings, "RELAY_AUTH_ENABLED", False) or getattr(settings, "relay_auth_enabled", False))
    if not enabled:
        return

    expected = _get_expected_key(settings)

    # If Authorization exists, treat it as an attempt and validate scheme first.
    authz = headers.get("authorization")
    if authz:
        if not authz.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Authorization header must use Bearer scheme")
        token = authz.split(" ", 1)[1].strip()
        if not expected or token != expected:
            raise HTTPException(status_code=401, detail="Invalid relay key")
        return

    # Otherwise, fall back to configured header (default x-relay-key)
    header_key = get_auth_header_key(settings)
    if header_key == "authorization":
        # No Authorization header provided at all
        raise HTTPException(status_code=401, detail="Missing relay key")

    provided = headers.get(header_key)
    if not provided:
        raise HTTPException(status_code=401, detail="Missing relay key")

    if not expected or provided != expected:
        raise HTTPException(status_code=401, detail="Invalid relay key")
