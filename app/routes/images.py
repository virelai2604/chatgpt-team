from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/generations", methods=["POST"])
async def image_generations(request: Request):
    # Structured log for image generations
    try:
        body = await request.json()
        save_chat_request(
            role="user",  # or "system", as preferred
            content=str(body.get("prompt", "")),
            function_call_json="",
            metadata_json=str(body)
        )
    except Exception as ex:
        print("BIFL log error (image generations):", ex)
    # Universal raw logging handled in forward_openai
    return await forward_openai(request, "/v1/images/generations")
