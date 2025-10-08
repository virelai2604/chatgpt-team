from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/", methods=["POST"])
async def embeddings(request: Request):
    # Structured log for embeddings
    try:
        body = await request.json()
        save_chat_request(
            role="user",  # or "system" if preferred
            content=str(body.get("input", "")),
            function_call_json="",
            metadata_json=str(body)
        )
    except Exception as ex:
        print("BIFL log error (embeddings):", ex)
    # Universal raw logging handled in forward_openai
    return await forward_openai(request, "/v1/embeddings")
