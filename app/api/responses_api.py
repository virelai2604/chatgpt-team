import logging
from fastapi import APIRouter, Request, HTTPException
from app.api.forward_openai import forward_openai
from app.utils.db_logger import save_raw_request

logger = logging.getLogger("BIFL.ResponsesAPI")
router = APIRouter(prefix="/v1/responses", tags=["Responses"])

@router.post("")
async def create_response(request: Request):
    """Unified OpenAI-compatible endpoint for GPT-5, o-series, Sora, and multimodal models."""
    try:
        body = await request.json()
        model = body.get("model", "").lower()

        # Auto-enable compliant tool container for GPT-5 and compatible models
        if any(m in model for m in ["gpt-5", "gpt-4o", "o-series"]) and not body.get("tools"):
            body["tools"] = [{
                "type": "code_interpreter",
                "container": {"type": "auto"}
            }]
            logger.info(f"[ResponsesAPI] Auto-injected default tool container for model: {model}")

        # Persist raw request for audit/debug
        await save_raw_request("responses", body)
        logger.info(f"[ResponsesAPI] Forwarding model: {model}")

        # Forward to upstream OpenAI API
        return await forward_openai(request, override_body=body)

    except Exception as e:
        logger.error(f"[ResponsesAPI] Request forwarding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{response_id}")
async def get_response(response_id: str):
    """Retrieve a previously stored model response (placeholder)."""
    try:
        logger.info(f"[ResponsesAPI] Retrieving response ID: {response_id}")
        return {
            "id": response_id,
            "object": "response",
            "status": "completed",
            "model": "gpt-5",
            "output": [{"type": "text", "content": "This is a stored example response."}],
            "usage": {"input_tokens": 58, "output_tokens": 132, "total_tokens": 190},
            "created": "2025-10-26T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"[ResponsesAPI] Retrieval failed: {e}")
        raise HTTPException(status_code=404, detail="Response not found")

@router.get("/schema")
async def get_schema():
    """Expose /v1/responses schema for introspection."""
    return {
        "endpoint": "/v1/responses",
        "fields": {
            "model": "string (required)",
            "input": "string | array | multimodal",
            "tools": "array (optional)",
            "tool_choice": "string (optional)",
            "stream": "boolean (optional)",
            "reasoning": "object (optional)",
            "background": "boolean (optional)"
        },
        "compatible_models": [
            "gpt-5", "gpt-5-pro", "gpt-4o", "gpt-4o-mini", "gpt-4.1", "sora-2-pro"
        ]
    }
