from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/assistants")

# v2 endpoints: CRUD for assistants
@router.post("")
async def create_assistant(request: Request):
    return await forward_openai(request, "/v1/assistants")

@router.get("")
async def list_assistants(request: Request):
    return await forward_openai(request, "/v1/assistants")

@router.get("/{assistant_id}")
async def get_assistant(request: Request, assistant_id: str):
    return await forward_openai(request, f"/v1/assistants/{assistant_id}")

@router.patch("/{assistant_id}")
async def update_assistant(request: Request, assistant_id: str):
    return await forward_openai(request, f"/v1/assistants/{assistant_id}")

# Deprecated v1 endpoints: mark as gone
@router.post("/attach_file")
async def deprecated_attach_file(request: Request):
    return JSONResponse(
        {"error": "Deprecated in v2. Use thread/message file upload."}, status_code=410
    )

@router.get("/list_files")
async def deprecated_list_files(request: Request):
    return JSONResponse(
        {"error": "Deprecated in v2. Use thread/message file upload."}, status_code=410
    )
