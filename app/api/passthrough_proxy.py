# app/api/passthrough_proxy.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward import forward_openai
from app.utils.db_logger import save_raw_request

router = APIRouter()

DENYLIST_PREFIXES = [
    "/v1/completions",
    "/v1/chat/completions",
    "/v1/assistants",
    "/v1/threads",
    "/v1/moderations",
    "/v1/fine_tuning/jobs",
    "/v1/organization/costs",
    "/v1/batches",
    "/v1/certificates",
    "/v1/audit_logs",
    "/v1/videos",
    "/v1/tools",  # standalone tools route deprecated in BIFL v2.1
]

def _should_block(path: str) -> bool:
    return any(path.startswith(p) for p in DENYLIST_PREFIXES)

@router.api_route("/v1/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def passthrough(request: Request, full_path: str):
    """
    BIFL-grade passthrough with legacy endpoint denylist.
    """
    endpoint = f"/v1/{full_path}"

    # 1) Hard block legacy endpoints so they can't slip through the catch-all
    if _should_block(endpoint):
        return JSONResponse(
            status_code=410,
            content={
                "error": {
                    "type": "legacy_endpoint",
                    "message": f"Endpoint '{endpoint}' is disabled in BIFL v2.1. Use /v1/responses (with tools[]) instead."
                }
            }
        )

    # 2) normal logging + forward
    raw_body = await request.body()
    headers_json = str(dict(request.headers))
    save_raw_request(endpoint=endpoint, raw_body=raw_body, headers_json=headers_json)
    return await forward_openai(request, endpoint)
