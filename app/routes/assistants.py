from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def assistants(request: Request):
    # Structured log for assistant creation (POST only)
    if request.method == "POST":
        try:
            body = await request.json()
            save_chat_request(
                role="assistant",  # Can use a more descriptive role if desired
                content=str(body),
                function_call_json="",
                metadata_json=str(body)
            )
        except Exception as ex:
            print("BIFL log error (assistants POST):", ex)
    # Universal raw logging is handled in forward_openai
    return await forward_openai(request, "/v1/assistants")

@router.api_route("/{assistant_id}", methods=["GET", "POST", "DELETE"])
async def assistant_by_id(request: Request, assistant_id: str):
    # Structured log for updating or deleting an assistant
    if request.method in ("POST", "DELETE"):
        try:
            body = await request.json() if request.method == "POST" else {}
            save_chat_request(
                role="assistant",
                content=str(body),
                function_call_json="",
                metadata_json=str(body)
            )
        except Exception as ex:
            print("BIFL log error (assistants by ID):", ex)
    return await forward_openai(request, f"/v1/assistants/{assistant_id}")
from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def assistants(request: Request):
    # Structured log for assistant creation (POST only)
    if request.method == "POST":
        try:
            body = await request.json()
            save_chat_request(
                role="assistant",  # Can use a more descriptive role if desired
                content=str(body),
                function_call_json="",
                metadata_json=str(body)
            )
        except Exception as ex:
            print("BIFL log error (assistants POST):", ex)
    # Universal raw logging is handled in forward_openai
    return await forward_openai(request, "/v1/assistants")

@router.api_route("/{assistant_id}", methods=["GET", "POST", "DELETE"])
async def assistant_by_id(request: Request, assistant_id: str):
    # Structured log for updating or deleting an assistant
    if request.method in ("POST", "DELETE"):
        try:
            body = await request.json() if request.method == "POST" else {}
            save_chat_request(
                role="assistant",
                content=str(body),
                function_call_json="",
                metadata_json=str(body)
            )
        except Exception as ex:
            print("BIFL log error (assistants by ID):", ex)
    return await forward_openai(request, f"/v1/assistants/{assistant_id}")
