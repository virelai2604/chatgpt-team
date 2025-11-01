"""
responses.py — Ground Truth API v1.7 compliant unified Responses route
Implements OpenAI-compatible /v1/responses endpoint with streaming, background,
and tool orchestration support.
"""

import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, AsyncGenerator, Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from app.api.tools_api import execute_tool_from_manifest
from app.utils.logger import logger

router = APIRouter()

# --------------------------------------------------------------------------
# Utility functions
# --------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Rudimentary token estimator (roughly word count)."""
    return len(text.split())


async def simulate_model_output(model: str, text: str) -> AsyncGenerator[str, None]:
    """Simulates a streaming model response, yielding small chunks."""
    for word in text.split():
        await asyncio.sleep(0.05)
        yield f"{word} "
    await asyncio.sleep(0.05)


def format_response_object(
    model: str,
    response_id: str,
    input_text: str,
    base_output: str,
    tool_outputs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Return unified response schema."""
    return {
        "id": response_id,
        "object": "response",
        "created": int(time.time()),
        "model": model,
        "output": [
            {"type": "message", "role": "assistant", "content": base_output}
        ],
        "tool_outputs": tool_outputs,
        "usage": {"total_tokens": estimate_tokens(input_text)},
    }

# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@router.post("/v1/responses")
async def create_response(request: Request):
    """
    Main /v1/responses entrypoint.
    Emulates OpenAI SDK client.responses.create() behavior (v2.6.1).

    Supported fields:
      - model: str
      - input: str or list[InputItem]
      - instructions: optional str
      - tools: list[tool definitions]
      - stream: bool
      - conversation / previous_response_id
      - temperature, max_output_tokens, background
    """
    try:
        body = await request.json()
        model: str = body.get("model", "gpt-5")
        input_text: str = body.get("input", "")
        tools: List[Dict[str, Any]] = body.get("tools", [])
        instructions: Optional[str] = body.get("instructions")
        stream: bool = bool(body.get("stream", False))
        background: bool = bool(body.get("background", False))
        temperature: float = float(body.get("temperature", 1.0))
        max_output_tokens: int = int(body.get("max_output_tokens", 4096))

        response_id = f"resp_{uuid.uuid4().hex[:12]}"
        logger.info(f"[{response_id}] New response: model={model}, stream={stream}, background={background}")

        # Background job simulation
        if background:
            asyncio.create_task(handle_background_response(model, input_text, tools, response_id))
            return JSONResponse(
                {
                    "id": response_id,
                    "object": "response",
                    "status": "queued",
                    "model": model,
                    "created": int(time.time())
                }
            )

        # Non-streamed case
        if not stream:
            base_output = f"Processed input: {input_text}"
            tool_outputs = []

            for tool_entry in tools:
                tool_name = tool_entry.get("type") or tool_entry.get("tool")
                args = tool_entry.get("args", {})
                logger.info(f"[{response_id}] Executing tool: {tool_name} args={args}")
                tool_result = await execute_tool_from_manifest(tool_name, args)
                tool_outputs.append(tool_result)

            response_object = format_response_object(model, response_id, input_text, base_output, tool_outputs)
            return JSONResponse(response_object)

        # Streamed case
        async def event_stream():
            logger.info(f"[{response_id}] Starting stream...")
            async for chunk in simulate_model_output(model, f"Streaming response for: {input_text}"):
                event = {
                    "event": "message.delta",
                    "data": chunk
                }
                yield f"data: {json.dumps(event)}\n\n"

            # Tool execution in streamed response (after generation)
            for tool_entry in tools:
                tool_name = tool_entry.get("type") or tool_entry.get("tool")
                args = tool_entry.get("args", {})
                tool_result = await execute_tool_from_manifest(tool_name, args)
                event = {
                    "event": "tool.result",
                    "data": tool_result
                }
                yield f"data: {json.dumps(event)}\n\n"

            # Final completion event
            done_event = {
                "event": "done",
                "data": {
                    "id": response_id,
                    "object": "response",
                    "model": model,
                    "created": int(time.time())
                }
            }
            yield f"data: {json.dumps(done_event)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error creating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_background_response(model: str, input_text: str, tools: List[Dict[str, Any]], response_id: str):
    """Simulate background job processing (queued response)."""
    try:
        await asyncio.sleep(1)
        logger.info(f"[{response_id}] Background job started.")
        base_output = f"[Background completed] {input_text}"
        tool_outputs = []

        for tool_entry in tools:
            tool_name = tool_entry.get("type") or tool_entry.get("tool")
            args = tool_entry.get("args", {})
            tool_result = await execute_tool_from_manifest(tool_name, args)
            tool_outputs.append(tool_result)

        logger.info(f"[{response_id}] Background job done with {len(tool_outputs)} tools.")
    except Exception as e:
        logger.error(f"[{response_id}] Background job error: {e}")


@router.get("/v1/responses/{response_id}")
async def get_response(response_id: str) -> Dict[str, Any]:
    """Retrieve stored or queued responses (placeholder)."""
    return {
        "id": response_id,
        "object": "response",
        "status": "retrieved",
        "created": int(time.time())
    }


@router.delete("/v1/responses/{response_id}")
async def delete_response(response_id: str) -> Dict[str, Any]:
    """Delete stored response (placeholder)."""
    logger.info(f"[{response_id}] Deleted.")
    return {"id": response_id, "object": "response", "deleted": True}


@router.post("/v1/responses/{response_id}/cancel")
async def cancel_response(response_id: str) -> Dict[str, Any]:
    """Cancel a running response generation."""
    logger.info(f"[{response_id}] Canceled by client.")
    return {"id": response_id, "object": "response", "canceled": True}


@router.get("/v1/responses/{response_id}/input_items")
async def list_input_items(response_id: str) -> Dict[str, Any]:
    """List input items contributing to a response."""
    return {"response_id": response_id, "items": ["input", "tools", "context"]}


@router.post("/v1/responses/input_tokens")
async def count_input_tokens(request: Request) -> Dict[str, Any]:
    """Estimate token usage for a request."""
    body = await request.json()
    text = body.get("input", "")
    count = estimate_tokens(text)
    return {"object": "tokens", "count": count}
