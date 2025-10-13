from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/", methods=["POST"])
async def batch_create(request: Request):
    """Create a new batch job (BIFL v2 style)."""
    try:
        body = await request.json()
        save_chat_request(
            role="system",  # or "batch"
            content=str(body),
            function_call_json="",
            metadata_json=str(body)
        )
    except Exception as ex:
        print("[BIFL] Batch Create Log Error:", ex)
    return await forward_openai(request, "/v1/batch")

@router.api_route("/{batch_id}", methods=["GET"])
async def batch_by_id(request: Request, batch_id: str):
    """Get batch status/details by ID."""
    return await forward_openai(request, f"/v1/batch/{batch_id}")
