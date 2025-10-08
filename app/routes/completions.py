from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/", methods=["POST"])
async def completions(request: Request):
    # Structured semantic logging
    try:
        body = await request.json()
        prompt = body.get("prompt", "")
        # "role" is not always present for /completions, so use "user" or leave blank
        save_chat_request(
            role="user",
            content=str(prompt),
            function_call_json="",  # completions endpoint does not use function_call
            metadata_json=str(body)
        )
    except Exception as ex:
        print("BIFL log error (completions):", ex)

    # Universal raw logging is handled in forward_openai
    return await forward_openai(request, "/v1/completions")
