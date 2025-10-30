from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1/conversations", tags=["Conversations"])

@router.get("")
async def list_conversations():
    return JSONResponse({"object": "list", "data": []})

@router.post("")
async def create_conversation(payload: dict):
    """Mock endpoint to maintain compatibility with ChatGPT UI clients."""
    return JSONResponse({"id": "conv_mock", "object": "conversation", "status": "created"})
