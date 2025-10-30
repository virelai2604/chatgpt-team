"""
app/middleware/validation.py
-------------------------------------------------------
Ground-truth schema validation middleware for /v1/responses
Ensures incoming requests conform to OpenAI’s official spec.
-------------------------------------------------------
"""

import json
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jsonschema import validate, ValidationError

# Simplified but faithful OpenAI “ground truth” /v1/responses schema
# (mirrors fields in the API Reference PDF)
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "model": {"type": "string"},
        "input": {
            "oneOf": [
                {"type": "string"},
                {
                    "type": "array",
                    "items": {"type": "string"}
                }
            ]
        },
        "max_output_tokens": {"type": "integer"},
        "parallel_tool_calls": {"type": "boolean"},
        "store": {"type": "boolean"},
        "tools": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "name": {"type": "string"},
                    "function": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "parameters": {"type": "object"}
                        },
                        "required": ["name", "parameters"]
                    }
                },
                "required": ["type", "name", "function"]
            }
        },
        "stream": {"type": "boolean"}
    },
    "required": ["model", "input"],
    "additionalProperties": True
}


class ResponseValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate /v1/responses payloads before forwarding."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path.endswith("/v1/responses") and request.method == "POST":
            try:
                body = await request.json()
                validate(instance=body, schema=RESPONSE_SCHEMA)
            except ValidationError as e:
                # strict ground-truth error schema
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "invalid_request_error",
                        "message": f"Schema validation failed: {e.message}",
                        "path": list(e.path),
                        "validator": e.validator
                    }
                )
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "invalid_json",
                        "message": "Body must be valid JSON matching OpenAI schema."
                    }
                )
        return await call_next(request)
