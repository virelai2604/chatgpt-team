from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/", methods=["GET"])
async def list_models(request: Request):
    try:
        save_chat_request(
            role="system",
            content="list_models",
            function_call_json="",
            metadata_json="{}"
        )
    except Exception as ex:
        print("BIFL log error (list models):", ex)
    return await forward_openai(request, "/v1/models")

@router.api_route("/{model}", methods=["GET"])
async def retrieve_model(request: Request, model: str):
    try:
        save_chat_request(
            role="system",
            content=f"retrieve_model: {model}",
            function_call_json="",
            metadata_json="{}"
        )
    except Exception as ex:
        print("BIFL log error (retrieve model):", ex)
    return await forward_openai(request, f"/v1/models/{model}")
