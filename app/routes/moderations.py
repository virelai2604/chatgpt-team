# app/routes/moderations.py
# BIFL v2.2 — Unified Moderation API
# Compatible with GPT-5 moderation models and local fallback.

import re
import time
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from app.api.forward import forward_openai


router = APIRouter(prefix="/v1/moderations", tags=["Moderations"])

# === Basic local heuristic filters (fallback) ===
LOCAL_RULES = {
    "violence": re.compile(r"\b(kill|attack|shoot|murder|torture)\b", re.IGNORECASE),
    "hate": re.compile(r"\b(hate|racist|bigot|slur|discriminate)\b", re.IGNORECASE),
    "sexual": re.compile(r"\b(sex|porn|nude|explicit|fetish)\b", re.IGNORECASE),
    "self_harm": re.compile(r"\b(suicide|cut|harm myself|kill myself)\b", re.IGNORECASE),
}


def local_moderation_check(text: str) -> Dict[str, Any]:
    """Simple heuristic classifier if GPT moderation model unavailable."""
    categories = {k: bool(p.search(text)) for k, p in LOCAL_RULES.items()}
    flagged = any(categories.values())
    return {
        "id": f"mod_{int(time.time() * 1000)}",
        "model": "local-fallback-moderation",
        "results": [{"flagged": flagged, "categories": categories}],
    }


# === Routes ===

@router.post("/")
async def moderate_text(body: Dict[str, Any] = Body(...)):
    """
    Perform text moderation.
    Automatically uses GPT-5 moderation model via relay,
    falls back to local regex filter if relay is unavailable.
    """
    input_text = body.get("input")
    model = body.get("model", "omni-moderation-latest")

    if not input_text:
        raise HTTPException(status_code=400, detail="Missing input text for moderation")

    try:
        relay = await forward_openai(
            path="/v1/moderations",
            method="POST",
            json={"input": input_text, "model": model},
        )
        if relay and "results" in relay:
            return JSONResponse(content=relay)
        raise Exception("Empty moderation response")
    except Exception as e:
        print(f"[WARN] Moderation relay failed, using local fallback: {e}")
        local_result = local_moderation_check(input_text)
        return JSONResponse(content=local_result)


@router.get("/rules")
async def get_local_rules():
    """List currently active local moderation regex patterns."""
    return JSONResponse(content={
        "object": "moderation_rules",
        "patterns": list(LOCAL_RULES.keys()),
        "updated": int(time.time())
    })


# === Tool integration for /v1/responses ===
async def execute_moderation_tool(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool entrypoint for /v1/responses moderation checks.
    Example:
      { "type": "moderation_check", "parameters": {"text": "example"} }
    """
    try:
        params = tool.get("parameters", {})
        text = params.get("text", "")
        model = params.get("model", "omni-moderation-latest")

        relay = await forward_openai(
            path="/v1/moderations",
            method="POST",
            json={"input": text, "model": model},
        )
        return {"type": "moderation_check", "results": relay.get("results", [])}
    except Exception as e:
        # Fallback to local moderation
        local = local_moderation_check(params.get("text", ""))
        return {"type": "moderation_check", "results": local.get("results", []), "error": str(e)}
