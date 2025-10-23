# app/routes/responses.py
import os, json
import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.api.forward import forward_openai            # reuse proxy for streaming/passthrough
from app.routes.services.tool_registry import collect_tool_results

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")

router = APIRouter(tags=["core"])

OPENAI_BASE = "https://api.openai.com"
MAX_TOOL_ROUNDS = 3  # cap re-entry to avoid loops

def _auth_headers() -> dict:
    h = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENAI_ORG_ID:
        h["OpenAI-Organization"] = OPENAI_ORG_ID
    return h

@router.post("/v1/responses")
async def create_response(request: Request):
    """
    Non-stream: run a local tool loop if the model issues function calls.
    Stream: passthrough to OpenAI so SSE events flow unmodified.
    """
    body = await request.json()
    if body.get("stream") is True:
        # Let the proxy stream SSE; it already handles headers and errors.
        return await forward_openai(request, "/v1/responses")

    # Non-stream: request -> (function_call?) -> execute tools -> post tool_result -> repeat
    headers = _auth_headers()
    async with httpx.AsyncClient(timeout=None) as client:
        # 1) initial call
        r = await client.post(f"{OPENAI_BASE}/v1/responses", headers=headers, json=body)
        try:
            data = r.json()
        except Exception:
            return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type"))

        rounds = 0
        while rounds < MAX_TOOL_ROUNDS:
            tool_results = await collect_tool_results(data)
            if not tool_results:
                break
            follow_up = {
                "model": body["model"],
                "previous_response_id": data["id"],    # continue same conversation state
                "input": tool_results
            }
            r2 = await client.post(f"{OPENAI_BASE}/v1/responses", headers=headers, json=follow_up)
            data = r2.json()
            rounds += 1

        # Final model output after tool execution (or first call if no tools)
        return JSONResponse(content=data, status_code=r.status_code)

# Everything else under /v1/responses/* is proxied (retrieve, delete, cancel, input_items)
@router.get("/v1/responses/{response_id}")
async def get_response(request: Request, response_id: str):
    return await forward_openai(request, f"/v1/responses/{response_id}")

@router.delete("/v1/responses/{response_id}")
async def delete_response(request: Request, response_id: str):
    return await forward_openai(request, f"/v1/responses/{response_id}")

@router.post("/v1/responses/{response_id}/cancel")
async def cancel_response(request: Request, response_id: str):
    return await forward_openai(request, f"/v1/responses/{response_id}/cancel")

@router.get("/v1/responses/{response_id}/input_items")
async def list_input_items(request: Request, response_id: str):
    return await forward_openai(request, f"/v1/responses/{response_id}/input_items")
