from __future__ import annotations

import asyncio
import inspect
import weakref
from dataclasses import dataclass
from typing import Dict

import httpx
from openai import AsyncOpenAI

from app.core.config import settings


@dataclass(slots=True)
class _LoopClients:
    loop_ref: weakref.ReferenceType[asyncio.AbstractEventLoop]
    httpx_client: httpx.AsyncClient
    openai_client: AsyncOpenAI


# Keyed by id(loop). We keep a weakref to detect stale loops.
_LOOP_CLIENTS: Dict[int, _LoopClients] = {}


def _cleanup_stale_loops() -> None:
    stale: list[int] = []
    for key, entry in _LOOP_CLIENTS.items():
        loop = entry.loop_ref()
        if loop is None or loop.is_closed():
            stale.append(key)

    # Best-effort: we cannot safely await close here (sync function).
    # The next get() call will create fresh clients.
    for key in stale:
        _LOOP_CLIENTS.pop(key, None)


def _timeout_seconds() -> float:
    """Resolve a single upstream timeout budget in seconds.

    Priority:
      1) settings.PROXY_TIMEOUT (explicit upstream budget)
      2) settings.timeout_seconds (normalized helper)
      3) 60.0 fallback
    """
    value = getattr(settings, "PROXY_TIMEOUT", None) or getattr(settings, "timeout_seconds", None) or 60
    try:
        seconds = float(value)
    except Exception:
        seconds = 60.0

    # Guardrails: non-positive values are treated as fallback.
    if seconds <= 0:
        return 60.0

    return seconds


def _httpx_timeout() -> httpx.Timeout:
    # Apply the same timeout to connect/read/write/pool for now.
    # If you later want "no read timeout" for SSE/streaming, adjust here.
    return httpx.Timeout(_timeout_seconds())


def _create_openai_client() -> AsyncOpenAI:
    """Create an AsyncOpenAI client with version-safe kwargs.

    We intentionally keep this conservative:
      - Only pass kwargs that exist in the installed openai-python version.
      - Avoid binding our own httpx.AsyncClient unless we are certain the SDK
        accepts it (SDK changes between versions).
    """

    base_kwargs = {
        "api_key": settings.openai_api_key,
        "base_url": _sdk_base_url(str(settings.openai_base_url)),
        "max_retries": getattr(settings, "max_retries", 3),
        "timeout": _timeout_seconds(),
    }

    # Optional organization support
    org = getattr(settings, "openai_organization", "")
    if org:
        base_kwargs["organization"] = org

    # Filter by signature for cross-version compatibility.
    sig = inspect.signature(AsyncOpenAI.__init__)
    kwargs = {k: v for k, v in base_kwargs.items() if k in sig.parameters}

    return AsyncOpenAI(**kwargs)


async def _maybe_aclose(obj: object) -> None:
    """Close an object that may expose close()/aclose() sync or async."""

    for method_name in ("aclose", "close"):
        meth = getattr(obj, method_name, None)
        if not callable(meth):
            continue

        try:
            result = meth()
        except TypeError:
            # Unexpected signature; ignore.
            continue

        if inspect.isawaitable(result):
            await result
        return


def get_async_httpx_client() -> httpx.AsyncClient:
    """Return an AsyncClient that is safe under pytest's function-scoped event loops.

    Why:
      - pytest-asyncio (STRICT) often creates a new loop per test.
      - Reusing a single global AsyncClient across loops can trigger
        'RuntimeError: Event loop is closed'.
    """

    _cleanup_stale_loops()

    loop = asyncio.get_running_loop()
    key = id(loop)

    entry = _LOOP_CLIENTS.get(key)
    if entry is not None and not entry.httpx_client.is_closed:
        return entry.httpx_client

    client = httpx.AsyncClient(
        timeout=_httpx_timeout(),
        follow_redirects=True,
    )

    openai_client = _create_openai_client()

    _LOOP_CLIENTS[key] = _LoopClients(
        loop_ref=weakref.ref(loop),
        httpx_client=client,
        openai_client=openai_client,
    )
    return client


def get_async_openai_client() -> AsyncOpenAI:
    _cleanup_stale_loops()

    loop = asyncio.get_running_loop()
    key = id(loop)

    entry = _LOOP_CLIENTS.get(key)
    if entry is not None:
        return entry.openai_client

    # Ensure both clients exist together.
    _ = get_async_httpx_client()
    return _LOOP_CLIENTS[key].openai_client


async def aclose_clients_for_current_loop() -> None:
    loop = asyncio.get_running_loop()
    key = id(loop)
    entry = _LOOP_CLIENTS.pop(key, None)
    if entry is None:
        return

    if not entry.httpx_client.is_closed:
        await entry.httpx_client.aclose()

    await _maybe_aclose(entry.openai_client)


async def aclose_all_clients() -> None:
    entries = list(_LOOP_CLIENTS.items())
    _LOOP_CLIENTS.clear()

    for _, entry in entries:
        if not entry.httpx_client.is_closed:
            await entry.httpx_client.aclose()
        await _maybe_aclose(entry.openai_client)


def _sdk_base_url(base_url: str) -> str:
    """Normalize base_url for the OpenAI Python SDK.

    AsyncOpenAI expects a base_url that typically includes /v1.

    We accept either:
      - https://api.openai.com
      - https://api.openai.com/v1

    and normalize to .../v1.
    """

    b = base_url.rstrip("/")
    if not b.endswith("/v1"):
        b = f"{b}/v1"
    return b
