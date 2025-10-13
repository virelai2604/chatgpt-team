from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_raw_request

router = APIRouter()

@router.api_route("/v1/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def passthrough(request: Request, full_path: str):
    """
    BIFL-grade: Logs every unmatched /v1/* request (all methods), preserving all headers and body bytes,
    then relays to the OpenAI API.
    """
    raw_body = await request.body()
    headers_json = str(dict(request.headers))
    save_raw_request(
        endpoint=f"/v1/{full_path}",
        raw_body=raw_body,
        headers_json=headers_json
    )
    endpoint = f"/v1/{full_path}"
    return await forward_openai(request, endpoint)
