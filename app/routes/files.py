# app/routes/files.py

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    prefix="/files",
    tags=["files"],
)


@router.api_route(
    "",
    methods=["GET", "POST"],
)
@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_files(request: Request, path: str = "") -> Response:
    """
    Catch-all proxy for OpenAI Files API.

    Examples:
      - GET  /v1/files                -> GET  /files
      - POST /v1/files                -> POST /files
      - GET  /v1/files/{file_id}      -> GET  /files/{file_id}
      - DELETE /v1/files/{file_id}    -> DELETE /files/{file_id}
      - POST /v1/files/{file_id}/...  -> POST /files/{file_id}/...

    The actual forwarding logic lives in `forward_openai_request`, which:
      - Clones method, headers, query params, and body.
      - Normalises the path (usually stripping the `/v1` prefix).
      - Sends to OpenAI base_url using your configured HTTP client.
    """
    return await forward_openai_request(request)
