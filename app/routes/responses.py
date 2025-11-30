# app/routes/responses.py

from fastapi import APIRouter, Request, Response
from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    POST /v1/responses
    Main chat/agent entrypoint.
    """
    logger.info("→ [responses] POST %s", request.url.path)
    return await forward_openai_request(request)
