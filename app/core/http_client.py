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


_LOOP_CLIENTS: Dict[int, _LoopClients] = {}


def _cleanup_stale_loops() -> None:
    stale: list[int] = []
    for key, entry in _LOOP_CLIENTS.items():
        loop = entry.loop_ref()
        if loop is None or loop.is_closed():
            stale.append(key)
    for key in stale:
        _LOOP_CLIENTS.pop(key, None)


def _timeout_seconds() -> float:
    """
    Resolve a single upstream timeout budget in seconds.
    Prefers the canonical config property `proxy_timeout_seconds`.
    """
    value = (
        getattr(settings, "proxy_timeout_seconds", None)
        or getattr(settings, "PROXY_TIMEOUT_SECONDS", None)
        or getattr(settings, "HTTP_TIMEOUT_SECONDS", None)
        or getattr(settings, "timeout_seconds", None)
        or 60
    )
    try:
        seconds = float(value)
    except Exception:
        seconds = 60.0
    return seconds if seconds > 0 else 60.0


def _httpx_timeout() -> httpx.Timeout:
    return httpx.Timeout(_timeout_seconds())


def _sdk_base_url(base_url: str) -> str:
    b = base_url.rstrip("/")
    if not b.endswith("/v1"):
        b = f"{b}/v1"
    return b


def _create_openai_client() -> AsyncOpenAI:
    """
    Create an AsyncOpenAI client with version-safe kwargs by filtering args
    against the installed SDK signature.
    """
    base_kwargs = {
        "api_key": getattr(settings, "openai_api_key", ""),
        "base_url": _sdk_base_url(str(getattr(settings, "openai_base_url", "https://api.openai.com/v1"))),
        "max_retries": getattr(settings, "max_retries", 3),
        "timeout": _timeout_seconds(),
    }

    org = getattr(settings, "openai_organization", None) or getattr(settings, "OPENAI_ORGANIZATION", None)
    if org:
        base_kwargs["organization"] = org

    project = getattr(settings, "openai_project", None) or getattr(settings, "OPENAI_PROJECT", None)
    if project:
        # Some SDK versions accept `project=...`; signature filter keeps us safe.
        base_kwargs["project"] = project

    sig = inspect.signature(AsyncOpenAI.__init__)
    kwargs = {k: v for k, v in base_kwargs.items() if k in sig.parameters}

    return AsyncOpenAI(**kwargs)


async def _maybe_aclose(obj: object) -> None:
    for method_name in ("aclose", "close"):
        meth = getattr(obj, method_name, None)
        if not callable(meth):
            continue
        try:
            result = meth()
        except TypeError:
            continue
        if inspect.isawaitable(result):
            await result
        return


def get_async_httpx_client() -> httpx.AsyncClient:
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
