from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/", methods=["POST"])
async def moderations(request: Request):
    # Structured log for moderation
    try:
        body = await request.json()
        save_chat_request(
            role="user",
            content=str(body.get("input", "")),
            function_call_json="",
            metadata_json=str(body)
        )
    except Exception as ex:
        print("BIFL log error (moderations):", ex)
    # Universal raw logging handled in forward_openai
    return await forward_openai(request, "/v1/moderations")
