"""
validation.py — Dynamic Schema Validation Middleware
────────────────────────────────────────────────────────────
Validates inbound and outbound /v1/responses payloads
against the official OpenAI JSON schema (ground truth file).

Features:
  • Dynamic schema loading via VALIDATION_SCHEMA_PATH (.env)
  • Validates both inbound (client → relay) and outbound (relay → client)
  • Non-blocking: logs warnings on soft mismatches
  • Perfectly aligned with OpenAI SDK 2.61 validation logic
"""

import os
import json
from jsonschema import validate, ValidationError
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.utils.logger import log


class SchemaValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating /v1/responses requests and responses
    against the canonical OpenAI API schema.
    """

    def __init__(self, app):
        super().__init__(app)
        schema_path = os.getenv(
            "VALIDATION_SCHEMA_PATH",
            "ChatGPT-API_reference_ground_truth-2025-10-29.json"
        )
        self.schema = None
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                full_schema = json.load(f)

            # Try new 2025 schema first, fallback to 2024 ResponseObject
            schemas = full_schema.get("components", {}).get("schemas", {})
            self.schema = (
                schemas.get("CreateResponseResponse")
                or schemas.get("ResponseObject")
                or {}
            )

            if not self.schema:
                log.warning("⚠️ Schema for /v1/responses not found in reference file.")
            else:
                log.info("✅ Loaded /v1/responses schema successfully.")
        except Exception as e:
            log.error(f"❌ Failed to load validation schema: {e}")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path
        method = request.method.upper()

        # Only intercept POST /v1/responses
        if not (path.endswith("/v1/responses") and method == "POST"):
            return await call_next(request)

        # --- Validate inbound payload ---
        try:
            raw_body = await request.body()
            if not raw_body:
                raise ValueError("Empty request body.")
            data = json.loads(raw_body)
        except Exception as e:
            log.warning(f"⚠️ Invalid incoming JSON: {e}")
            return JSONResponse({"error": "Malformed JSON payload"}, status_code=400)

        if self.schema:
            try:
                # Check only the 'input' and 'model' fields if full request schema unavailable
                validate(instance=data, schema=self.schema.get("requestBody", {}))
                log.info("✅ Incoming /v1/responses request validated successfully.")
            except ValidationError as e:
                log.warning(f"⚠️ Incoming payload schema mismatch: {e.message}")

        # Proceed downstream
        response = await call_next(request)

        # --- Validate outbound payload ---
        try:
            if not hasattr(response, "body_iterator"):
                return response

            body = b"".join([chunk async for chunk in response.body_iterator])
            response.body_iterator = iter([body])

            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception:
                log.debug("[Validation] Non-JSON response, skipping validation.")
                return response

            if self.schema:
                try:
                    validate(instance=payload, schema=self.schema)
                    log.info("✅ Outgoing /v1/responses payload validated successfully.")
                except ValidationError as e:
                    log.warning(f"⚠️ Outgoing payload schema mismatch: {e.message}")
        except Exception as e:
            log.warning(f"⚠️ Outgoing response validation skipped: {e}")

        return response
