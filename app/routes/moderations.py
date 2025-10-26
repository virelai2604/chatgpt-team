# ==========================================================
# app/routes/moderations.py — BIFL v2.3.4-fp
# ==========================================================
# Unified moderation handler for OpenAI-compatible safety APIs.
# Supports GPT-5, omni-moderation models, and streaming JSON results.
# ==========================================================

from fastapi import APIRouter, Request, Response
from app.api.forward import forward_openai
from app.utils.db_logger import log_event
import json, re

router = APIRouter(prefix="/v1/moderations", tags=["Moderations"])

# ----------------------------------------------------------
# 🧩  Submit Moderation Request
# ----------------------------------------------------------
@router.post("")
async def create_moderation(request: Request):
    """
    Submit text or content for moderation analysis.
    Example:
      {
        "model": "omni-moderation-latest",
        "input": "Some content to evaluate",
        "stream": false
      }
    """
    response = await forward_openai(request, "/v1/moderations")
    try:
        await log_event("/v1/moderations", response.status_code, "moderation check")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🧠  Optional Local Fallback (regex-based)
# ----------------------------------------------------------
@router.post("/fallback")
async def local_moderation_fallback(request: Request):
    """
    Optional offline moderation fallback.
    Uses regex heuristics for obvious violations when OpenAI API unavailable.
    """
    body = await request.json()
    text = body.get("input", "")
    flagged = bool(re.search(r"(violence|hate|sexual|self-harm|terrorism|illegal)", text, re.I))
    result = {
        "id": "modlocal-" + re.sub(r"\\W+", "", text[:16]),
        "object": "moderation",
        "model": "local-fallback-v1",
        "results": [{"flagged": flagged, "categories": {"unsafe": flagged}}],
    }
    return Response(content=json.dumps(result), media_type="application/json")
