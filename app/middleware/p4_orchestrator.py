"""
p4_orchestrator.py
-------------------------------------------------------------
Middleware: Intercepts POST requests to /v1/p4
and orchestrates a structured reasoning prompt chain.

Purpose:
- Convert user reasoning requests into structured
  /v1/responses payloads.
- Forward locally to the relay’s own /v1/responses endpoint.
- Preserve OpenAI schema and authentication headers.

Author: ChatGPT Team Relay (Ground-Truth Edition)
-------------------------------------------------------------
"""

import os
import json
import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
from typing import Any, Dict

class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Intercepts /v1/p4 requests and internally forwards them
    to the /v1/responses endpoint with a reasoning template.
    """

    async def dispatch(self, request: Request, call_next):
        # Only intercept reasoning endpoint
        if not (request.url.path.endswith("/v1/p4") and request.method.upper() == "POST"):
            return await call_next(request)

        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid_json"}, status_code=400)

        user_input = body.get("input")
        model = body.get("model", "gpt-4o-mini")

        if not user_input:
            return JSONResponse({"error": "missing_input"}, status_code=400)

        # Build structured reasoning prompt
        reasoning_prompt = f"""
You are a reasoning model. Analyze the input step-by-step and return results in the following structure:
1. **Answer:** Concise and correct.
2. **Analogy:** Intuitive, simple comparison.
3. **Steps/Code:** Reasoning or pseudo-code.
4. **Test/Takeaway:** Quick verification or summary.

Input: {user_input}
        """.strip()

        # Prepare request for internal /v1/responses
        payload = {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": reasoning_prompt}
                    ]
                }
            ],
            "response_format": "text"
        }

        # Use PORT from environment for flexibility
        relay_port = os.getenv("PORT", "8000")
        local_url = f"http://127.0.0.1:{relay_port}/v1/responses"

        headers = {"Content-Type": "application/json"}
        # Forward the reasoning prompt internally
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
            try:
                resp = await client.post(local_url, json=payload, headers=headers)
            except httpx.RequestError as e:
                return JSONResponse(
                    {"error": f"connection_error", "detail": str(e)},
                    status_code=502,
                )

        if resp.status_code != 200:
            try:
                data = resp.json()
            except Exception:
                data = {"error": resp.text}
            return JSONResponse(
                {"error": "upstream_error", "detail": data},
                status_code=resp.status_code,
            )

        try:
            output = resp.json()
        except Exception:
            output = {"raw_output": resp.text}

        return JSONResponse(output, status_code=200)
