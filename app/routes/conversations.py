# ================================================================
# validation.py — Schema Validation Middleware
# ================================================================
# This layer ensures all requests follow OpenAI-compatible schema.
# It runs lightweight checks on required fields, disallowing malformed
# payloads that could otherwise propagate into downstream APIs.
# ================================================================

from fastapi import Request
from fastapi.responses import JSONResponse

REQUIRED_FIELDS = {
    "/v1/responses": ["model", "input"],
    "/v1/embeddings": ["input"],
}

async def validate_request(req: Request):
    """
    Validates that required fields exist in incoming payloads
    for known OpenAI endpoints.
    """
    path = req.url.path
    if req.method != "POST" or path not in REQUIRED_FIELDS:
        return None  # Skip validation for non-target endpoints

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({
            "error": {
                "message": "Malformed JSON body.",
                "type": "json_error",
            }
        }, status_code=400)

    missing = [k for k in REQUIRED_FIELDS[path] if k not in body]
    if missing:
        return JSONResponse({
            "error": {
                "message": f"Missing required fields: {', '.join(missing)}",
                "type": "validation_error",
                "code": "schema_violation"
            }
        }, status_code=400)

    return None
