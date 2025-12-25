from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from starlette.requests import Request

from app.core.config import settings


def _get_expected_key() -> str:
    key = (settings.RELAY_KEY or "").strip()
    if not key:
        raise HTTPException(status_code=500, detail="Server missing RELAY_KEY configuration")
    return key


def _extract_from_authorization(request: Request) -> Optional[str]:
    auth = (request.headers.get("Authorization") or "").strip()
    if not auth:
        return None

    # Enforce Bearer scheme so clients get an actionable message.
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header must use Bearer scheme")

    token = auth[7:].strip()
    return token or None


def _extract_from_custom_header(request: Request) -> Optional[str]:
    header_name = (settings.RELAY_AUTH_HEADER or "X-Relay-Key").strip()
    if not header_name:
        header_name = "X-Relay-Key"
    value = request.headers.get(header_name)
    return value.strip() if value else None


def check_relay_key(request: Request) -> None:
    """
    Validates relay authentication, raising HTTPException(401/500) when invalid.

    Accepted inputs:
      - Custom header (settings.RELAY_AUTH_HEADER, default: X-Relay-Key)
      - Authorization: Bearer <key>
    """
    provided = _extract_from_custom_header(request)
    if not provided:
        provided = _extract_from_authorization(request)

    if not provided:
        raise HTTPException(status_code=401, detail="Missing relay key")

    expected = _get_expected_key()
    if provided != expected:
        raise HTTPException(status_code=401, detail="Invalid relay key")
