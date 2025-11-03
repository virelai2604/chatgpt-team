"""
validation.py — Dynamic Schema Validation Middleware
────────────────────────────────────────────────────────────
Validates /v1/responses request and response payloads
against OpenAI’s official API schema (Ground Truth 2025-10).
"""

import os
import json
from jsonschema import validate, ValidationError
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.utils.logger import log

class SchemaValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for validating /v1/responses payloads."""

    def __init__(self, app):
        super().__init__(app)
        schema_path = os.getenv("VALIDATION_SCHEMA_PATH", "ChatGPT-API_reference_ground_truth-2025-10-29.json")
        self.schema = None
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                full_schema = json.load(f)
            schemas = full_schema.get("components", {}).get("schemas", {})
            self.schema = schemas.get("CreateResponseResponse") or schemas.get("ResponseObject") or {}
            log.info("✅ Validation schema loaded successfully.")
        except Exception as e:
            log.error(f"❌ Failed to load validation schema: {e}")
            self.schema = None

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path
        method = request.method.upper()

        if not (path.endswith("/v1/responses") and method == "POST"):
            return await call_next(request)

        # Validate inbound
        try:
            raw = await request.body()
            data = json.loads(raw or "{}")
            # Normalize SDK field aliases
            if "input_text" in data and "input" not in data:
                data["input"] = data.pop("input_text")
            if self.schema:
                validate(instance=data, schema=self.schema.get("requestBody", {}))
                log.info("✅ Inbound /v1/responses payload validated successfully.")
        except ValidationError as e:
            log.warning(f"⚠️ Inbound payload schema mismatch: {e.message}")
        except Exception as e:
            log.warning(f"⚠️ Could not validate inbound payload: {e}")

        # Continue request
        response = await call_next(request)

        # Validate outbound
        try:
            body = b"".join([chunk async for chunk in response.body_iterator])
            response.body_iterator = [body].__iter__()
            payload = json.loads(body.decode("utf-8"))
            if self.schema:
                validate(instance=payload, schema=self.schema)
                log.info("✅ Outbound /v1/responses payload validated successfully.")
        except ValidationError as e:
            log.warning(f"⚠️ Outbound payload schema mismatch: {e.message}")
        except Exception as e:
            log.warning(f"⚠️ Outbound validation skipped: {e}")

        return response
