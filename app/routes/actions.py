# app/routes/actions.py

from __future__ import annotations

import base64
from typing import Dict, Tuple

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.forward_openai import build_outbound_headers, build_upstream_url
from app.core.http_client import get_async_httpx_client

from app.core.config import settings

router = APIRouter(tags=["actions"])

_MAX_FILE_BYTES = 25 * 1024 * 1024


class FilesUploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose: str = Field(..., description="OpenAI file purpose, e.g. 'batch' or 'assistants'.")
    filename: str = Field(..., description="Filename for the uploaded file.")
    mime_type: str = Field(..., description="MIME type for the file, e.g. text/plain.")
    data_base64: str = Field(..., description="Base64-encoded file contents.")


def _filter_response_headers(headers: Dict[str, str]) -> Dict[str, str]:
    blocked = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",
        "content-encoding",
    }
    return {k: v for k, v in headers.items() if k.lower() not in blocked}


def _ping_payload() -> dict:
    """
    Canonical payload for ping-style endpoints.

    Tests assert at least:
      - data["status"] == "ok"            (for /actions/ping)
      - data["source"] == "chatgpt-team-relay"
      - data["app_mode"] non-empty
      - data["environment"] non-empty     (for /v1/actions/ping)
    """
    return {
        "source": "chatgpt-team-relay",
        "status": "ok",
        "app_mode": settings.APP_MODE,
        "environment": settings.ENVIRONMENT,
    }


def _relay_info_payloads() -> tuple[dict, dict]:
    """
    Build both the nested and flat relay-info payloads.

    Nested shape (for /v1/actions/relay_info):

        {
          "type": "relay.info",
          "relay": {
            "name": <relay_name>,
            "app_mode": <app_mode>,
            "environment": <environment>,
          },
          "upstream": {
            "base_url": <openai_base_url>,
            "default_model": <default_model>,
          },
        }

    Flat shape (for /actions/relay_info):

        {
          "relay_name": <relay_name>,
          "environment": <environment>,
          "app_mode": <app_mode>,
          "base_openai_api": <openai_base_url>,
        }

    The tests only assert that the relevant keys exist and are non-empty.
    """
    relay_name = settings.RELAY_NAME or "chatgpt-team-relay"
    app_mode = settings.APP_MODE
    environment = settings.ENVIRONMENT
    base_url = settings.OPENAI_API_BASE
    default_model = settings.DEFAULT_MODEL

    nested = {
        "type": "relay.info",
        "relay": {
            "name": relay_name,
            "app_mode": app_mode,
            "environment": environment,
        },
        "upstream": {
            "base_url": base_url,
            "default_model": default_model,
        },
    }

    flat = {
        "relay_name": relay_name,
        "environment": environment,
        "app_mode": app_mode,
        "base_openai_api": base_url,
    }

    return nested, flat


# ----- ping -----

@router.get("/actions/ping", summary="Simple local ping for tools/tests")
async def actions_ping_root() -> dict:
    """
    Simple ping at /actions/ping.

    tests/test_tools_and_actions_routes.py only checks that:
      - response.status_code == 200
      - response.json()["status"] == "ok"
    Extra fields are allowed.
    """
    return _ping_payload()


@router.get("/v1/actions/ping", summary="Local ping used by orchestrator tests")
async def actions_ping_v1() -> dict:
    """
    Ping under /v1/actions/ping.

    tests/test_actions_and_orchestrator.py requires:
      - status code 200
      - JSON contains non-empty source/status/app_mode/environment
    """
    return _ping_payload()


# ----- relay_info -----

@router.get("/actions/relay_info", summary="Flat relay info for tools")
async def actions_relay_info_root() -> dict:
    """
    Flat relay info at /actions/relay_info.

    tests/test_tools_and_actions_routes.py asserts:
      - data["relay_name"]
      - data["environment"]
      - data["app_mode"]
      - data["base_openai_api"]
    """
    _nested, flat = _relay_info_payloads()
    return flat


@router.get("/v1/actions/relay_info", summary="Structured relay info for orchestrator")
async def actions_relay_info_v1() -> dict:
    """
    Structured relay info at /v1/actions/relay_info.

    tests/test_actions_and_orchestrator.py asserts that:
      - data["type"] == "relay.info"
      - data["relay"]["name"] is non-empty
      - data["relay"]["app_mode"] is non-empty
      - data["relay"]["environment"] is non-empty
      - data["upstream"]["base_url"] is non-empty
      - data["upstream"]["default_model"] is non-empty
    """
    nested, _flat = _relay_info_payloads()
    return nested


@router.post("/v1/actions/files/upload", summary="Upload a file via base64 payload")
async def actions_files_upload(payload: FilesUploadRequest) -> Response:
    try:
        data = base64.b64decode(payload.data_base64, validate=True)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid data_base64: {exc}") from exc

    if len(data) > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds {_MAX_FILE_BYTES} bytes limit",
        )

    files: Dict[str, Tuple[str, bytes, str]] = {
        "file": (payload.filename, data, payload.mime_type),
    }
    form_data = {"purpose": payload.purpose}

    url = build_upstream_url("/v1/files")
    headers = build_outbound_headers({}, path_hint="/v1/files")

    client = get_async_httpx_client()
    try:
        resp = await client.post(url, headers=headers, data=form_data, files=files)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}") from exc

    filtered_headers = _filter_response_headers(dict(resp.headers))
    content_type = resp.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        return JSONResponse(
            content=resp.json(),
            status_code=resp.status_code,
            headers=filtered_headers,
        )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=filtered_headers,
        media_type=content_type or None,
    )
