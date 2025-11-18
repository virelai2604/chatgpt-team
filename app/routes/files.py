"""
files.py — /v1/files proxy
──────────────────────────
Thin, OpenAI-compatible proxy for file upload, listing, retrieval,
deletion, and content download.

Matches the official Files API surface:

  • GET    /v1/files
  • POST   /v1/files
  • GET    /v1/files/{file_id}
  • GET    /v1/files/{file_id}/content
  • DELETE /v1/files/{file_id}

The actual HTTP behavior (auth, multipart handling, streaming, errors)
is delegated to `forward_openai_request`, which is shared by all
proxied /v1/* endpoints in the relay.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["files"],
)


@router.api_route("/files", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def proxy_files_root(request: Request):
    """
    /v1/files

    GET:
      Lists files available to the API key, as defined by the OpenAI Files
      API (e.g., used for assistants, fine-tuning, batch, and vector stores).

    POST:
      Uploads a new file via multipart/form-data with fields like:
        - purpose
        - file (binary)
      and any other parameters supported by the upstream API.

    We do not implement any custom logic here; everything is forwarded to
    OpenAI via the shared forwarder to keep behavior perfectly aligned with
    the official spec and SDK behavior.
    """
    logger.info("→ [files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route("/files/{path:path}", methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"])
async def proxy_files_subpaths(path: str, request: Request):
    """
    /v1/files/{...} — catch-all for file sub-resources.

    This route covers, for example:

      • GET    /v1/files/{file_id}
            → Retrieve file metadata.

      • GET    /v1/files/{file_id}/content
            → Download the raw file content.

      • DELETE /v1/files/{file_id}
            → Delete a file.

    Any future sub-resources introduced under /v1/files/* are also
    automatically supported, because we delegate the full path and HTTP
    method to the upstream OpenAI API via `forward_openai_request`.
    """
    logger.info(
        "→ [files] %s %s (subpath=%s)",
        request.method,
        request.url.path,
        path,
    )
    return await forward_openai_request(request)
