"""
app/middleware/p4_orchestrator.py
-------------------------------------------------------
P4 Orchestrator Middleware — reasoning front-end for the
ChatGPT Team Relay.  Converts POST /v1/p4 calls into
ground-truth /v1/responses payloads.
-------------------------------------------------------
"""

import os
import httpx
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# -------------------------------------------------------------------
# Environment — drawn from .env to stay in sync with main.py
# -------------------------------------------------------------------
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8080")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")

# Structured reasoning header — this text never changes the schema,
# it only shapes the user prompt.
P4_PROMPT_HEADER = (
    "You are P4, the Cross-Domain Analogy Hybrid Developer (v2.0). "
    "Always follow this structure exactly:\n"
    "Answer → Analogy → Steps/Code → Test/Takeaway.\n\n"
)

# -------------------------------------------------------------------
# Middleware definition
# -------------------------------------------------------------------
class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """Intercepts /v1/p4 POST requests and relays them as
    valid /v1/responses payloads through the local OpenAI-compatible relay."""

    async def dispatch(self, request: Request, call_next):
        # Only handle the reasoning endpoint; all others pass through.
        if request.url.path.endswith("/v1/p4") and request.method.upper() == "POST":
            try:
                body = await request.json()
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "invalid_json",
                        "message": "Expected valid JSON body."
                    }
                )

            user_input = body.get("input", "")
            model      = body.get("model", "gpt-4o")

            if not user_input:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "missing_input",
                        "message": "Field 'input' is required."
                    }
                )

            # Compose a fully OpenAI-compliant /v1/responses payload.
            payload = {
                "model": model,
                "input": f"{P4_PROMPT_HEADER}User query: {user_input}",
                "stream": False
            }

            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }

            # Forward internally to the relay’s /v1/responses endpoint.
            async with httpx.AsyncClient(timeout=None) as client:
                resp = await client.post(
                    f"{OPENAI_BASE_URL}/v1/responses",
                    headers=headers,
                    json=payload
                )
                try:
                    data = resp.json()
                except Exception:
                    data = {"error": "relay_response_invalid", "content": resp.text}

            return JSONResponse(status_code=resp.status_code, content=data)

        # For all other routes, continue normal processing.
        return await call_next(request)
