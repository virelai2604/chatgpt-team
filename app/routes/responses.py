# app/routes/responses.py (conceptual summary)

from typing import Any, AsyncIterator, Dict
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from app.api.forward_openai import forward_responses_create
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["responses"])


async def _iter_sse_events(stream: Any) -> AsyncIterator[bytes]:
    import json

    async for event in stream:
        try:
            event_type = getattr(event, "type", None)

            if hasattr(event, "model_dump_json"):
                data_json = event.model_dump_json(exclude_none=True)
            elif hasattr(event, "model_dump"):
                data_json = json.dumps(event.model_dump(exclude_none=True))
            elif isinstance(event, dict):
                data_json = json.dumps(event)
            else:
                data_json = json.dumps({"data": str(event)})

            if event_type:
                chunk = f"event: {event_type}\ndata: {data_json}\n\n"
            else:
                chunk = f"data: {data_json}\n\n"
        except Exception as exc:
            # Defensive error event
            error_payload = json.dumps({
                "type": "response.error",
                "error": {
                    "message": f"Failed to serialize streaming event: {exc}",
                    "code": "relay_sse_serialization_error",
                },
            })
            chunk = f"event: response.error\ndata: {error_payload}\n\n"

        yield chunk.encode("utf-8")


@router.post("/responses")
async def create_response(
    body: Dict[str, Any] = Body(..., description="OpenAI Responses.create payload"),
) -> Any:
    logger.info("Incoming /v1/responses request")

    stream_param = body.get("stream")

    if stream_param:
        logger.info("Handling /v1/responses as streaming SSE request")
        upstream_stream = await forward_responses_create(body)

        return StreamingResponse(
            _iter_sse_events(upstream_stream),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    logger.info("Handling /v1/responses as non-streaming JSON request")
    return await forward_responses_create(body)
