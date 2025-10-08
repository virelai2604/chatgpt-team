from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def vector_stores(request: Request):
    if request.method == "POST":
        try:
            body = await request.json()
            save_chat_request(
                role="system",  # or "vector_store" if you want to differentiate
                content=str(body),
                function_call_json="",
                metadata_json=str(body)
            )
        except Exception as ex:
            print("BIFL log error (vector_stores POST):", ex)
    return await forward_openai(request, "/v1/vector_stores")
