# ================================================================
# validation.py — Schema Validation Middleware for ChatGPT Team Relay
# ================================================================
# Validates inbound /v1/responses and outbound responses
# against the OpenAI-compatible JSON schema.
#
# Features:
#   • Applies to /v1/responses requests
#   • Ensures well-formed JSON payloads
#   • Logs validation results and warnings
#   • Does not block traffic on soft failures (for dev flexibility)
# ================================================================

import json
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from jsonschema import validate, ValidationError

from app.utils.logger import logger


# ================================================================
# Schema Definition (Simplified OpenAI /v1/responses)
# ================================================================
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "object": {"type": "string"},
        "created_at": {"type": "number"},
        "model": {"type": "string"},
        "status": {"type": "string"},
        "output": {"type": "array"},
    },
    "required": ["id", "object", "model", "status"],
}


# ================================================================
# Middleware Class
# ================================================================
class SchemaValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates /v1/responses payloads against
    the OpenAI-compatible schema before and after relay processing.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path
        method = request.method.upper()

        # Only validate /v1/responses
        if not (path.endswith("/v1/responses") and method == "POST"):
            return await call_next(request)

        try:
            raw_body = await request.body()
            data = json.loads(raw_body)
        except Exception as e:
            logger.warning(f"⚠️ Invalid JSON in incoming request: {e}")
            return JSONResponse(
                status_code=400,
                content={"error": "Malformed JSON payload"},
            )

        # Validate incoming payload
        try:
            validate(instance=data, schema=RESPONSE_SCHEMA)
            logger.info("✅ Incoming /v1/responses payload validated successfully.")
        except ValidationError as e:
            logger.warning(f"⚠️ Incoming /v1/responses schema mismatch: {e.message}")

        # Continue processing
        response = await call_next(request)

        # Validate outgoing payload (if JSON)
        try:
            body = b"".join([chunk async for chunk in response.body_iterator])
            response.body_iterator = iter([body])

            payload = json.loads(body)
            validate(instance=payload, schema=RESPONSE_SCHEMA)
            logger.info("✅ Outgoing /v1/responses validated successfully.")
        except (json.JSONDecodeError, ValidationError):
            logger.warning("⚠️ Outgoing response did not match schema.")

        return response
