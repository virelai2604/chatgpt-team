# ================================================================
# responses.py — Unified Responses Endpoint
# ================================================================
# Emulates OpenAI’s /v1/responses, /responses, and /v1/responses:stream.
# Handles:
#   - Background responses (status="queued")
#   - Streaming SSE responses
#   - Synchronous tool invocations
# Ground truth aligned with OpenAI SDK 2.6.1
# ================================================================

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
import time, uuid, asyncio, json

router = APIRouter(tags=["responses"])

@router.post("/v1/responses")
async def create_response(req: Request):
    """
    Handles all variants: streaming, background, and synchronous responses.
    """
    body = await req.json()

    # Validation
    if not body.get("model") or not body.get("input"):
        return JSONResponse({
            "error": {
                "message": "Invalid request: 'model' and 'input' are required.",
                "type": "invalid_request_error"
            }
        }, status_code=400)

    # Background response path
    if body.get("background", False):
        return JSONResponse({
            "object": "response",
            "id": f"resp_{uuid.uuid4().hex[:8]}",
            "status": "queued"
        })

    # Streaming response path
    if body.get("stream", False):
        resp_id = f"resp_{uuid.uuid4().hex[:8]}"

        async def event_stream():
            # Create event
            yield f'data: {json.dumps({\
                "type": "response.created",\
                "response": {\
                    "id": resp_id,\
                    "object": "response",\
                    "model": "gpt-5",\
                    "status": "in_progress",\
                    "output": [{\
                        "type": "message",\
                        "role": "assistant",\
                        "content": [{"type": "output_text", "text": ""}]\
                    }]\
                }\
            })}\n\n'

            yield f'data: {json.dumps({"type": "response.started", "id": resp_id, "object": "response"})}\n\n'
            yield f'data: {json.dumps({"type": "response.output_item.added", "item": {"type": "message", "role": "assistant", "content": []}})}\n\n'
            yield f'data: {json.dumps({"type": "response.content_part.added", "output_index": 0, "part": {"type": "output_text", "text": ""}})}\n\n'

            for chunk in ["Hello from stream ", "chunk 1 ", "chunk 2"]:
                await asyncio.sleep(0.05)
                yield f'data: {json.dumps({"type": "response.output_text.delta", "output_index": 0, "content_index": 0, "delta": chunk})}\n\n'
                yield f'data: {json.dumps({"type": "message.delta", "delta": {"role": "assistant", "content": [{"type": "output_text", "text": chunk}]}})}\n\n'

            yield f'data: {json.dumps({\
                "type": "response.completed",\
                "response": {\
                    "id": resp_id,\
                    "object": "response",\
                    "model": "gpt-5",\
                    "status": "completed",\
                    "output": [{\
                        "type": "message",\
                        "role": "assistant",\
                        "content": [{"type": "output_text", "text": "stream complete"}]\
                    }]\
                }\
            })}\n\n'

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # Default synchronous response path
    tool_name = None
    if body.get("tools"):
        t = body["tools"][0]
        tool_name = t.get("type")

    output_text = f"Executed tool {tool_name or 'none'} successfully."

    return JSONResponse({
        "object": "response",
        "id": f"resp_{uuid.uuid4().hex[:8]}",
        "model": body["model"],
        "output": [{
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": output_text}]
        }],
        "tool_outputs": [{
            "tool": tool_name or "mock_tool",
            "status": "success",
            "output": {"result": "ok"}
        }],
        "usage": {"total_tokens": 5},
        "status": "completed"
    })


@router.post("/responses")
async def create_response_alias(req: Request):
    """Alias to /v1/responses for SDK backward compatibility."""
    return await create_response(req)


@router.post("/v1/responses:stream")
async def create_response_stream(req: Request):
    """Alias for OpenAI SDK's streaming endpoint."""
    return await create_response(req)


@router.post("/responses:stream")
async def create_response_stream_alias(req: Request):
    """Alias to /v1/responses:stream for compatibility."""
    return await create_response(req)
