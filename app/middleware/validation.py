"""
validation.py — Ground Truth API v1.7
Validates POST /v1/responses payloads against schema.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jsonschema
import json
from app.utils.logger import logger

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "model": {"type": "string"},
        "input": {"type": ["string", "array", "object"]},
        "instructions": {"type": ["string", "null"]},
        "tools": {"type": "array"},
        "stream": {"type": "boolean"},
        "temperature": {"type": ["number", "null"]},
        "max_output_tokens": {"type": ["number", "null"]},
        "tool_choice": {"type": ["string", "object", "null"]},
        "response_format": {"type": ["string", "object", "null"]}
    },
    "required": ["model", "input"]
}


class ResponseValidator(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/v1/responses" and request.method == "POST":
            try:
                body = await request.json()
                jsonschema.validate(body, RESPONSE_SCHEMA)
            except jsonschema.ValidationError as e:
                logger.error(f"Schema validation error: {e.message}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "message": f"Invalid request body: {e.message}",
                            "type": "invalid_request_error",
                            "param": e.path,
                            "code": "schema_violation",
                        }
                    },
                )
            except Exception as e:
                logger.error(f"Unexpected validation error: {e}")
                raise HTTPException(status_code=400, detail="Malformed JSON body")
        return await call_next(request)
