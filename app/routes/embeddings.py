from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/", methods=["POST"])
async def embeddings(request: Request):
    """Get embeddings for input(s) (BIFL v2 style)."""
    try:
        body = await request.json()
        save_chat_request(
            role="user",  # or "system"
            content=str(body.get("input", "")),
            function_call_json="",
            metadata_json=str(body)
        )
    except Exception as ex:
        print("[BIFL] Embeddings Log Error:", ex)
    return await forward_openai(request, "/v1/embeddings")
