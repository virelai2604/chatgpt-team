from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/completions", methods=["POST"])
async def chat_completions(request: Request):
    # Parse request for structured log (safe against any JSON input)
    try:
        body = await request.json()
        messages = body.get("messages", "")
        function_call = body.get("function_call", "")
        save_chat_request(
            role="user",  # or body.get("messages", [{}])[0].get("role", "user")
            content=str(messages),
            function_call_json=str(function_call),
            metadata_json=str(body)
        )
    except Exception as ex:
        # If request is not JSON or logging fails, still continue
        print("BIFL log error (chat):", ex)

    # Universal logging already handled in forward_openai
    return await forward_openai(request, "/v1/chat/completions")
