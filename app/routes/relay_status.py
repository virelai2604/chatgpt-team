# app/routes/relay_status.py — BIFL v2.3.4-fp
import os
from fastapi import APIRouter

router = APIRouter(prefix="/v1/relay_status", tags=["Relay Status"])

@router.get("")
async def status():
    return {
        "relay_name": "ChatGPT Team Relay",
        "bifl_version": "2.3.4-fp",
        "streaming_enabled": os.getenv("ENABLE_STREAM", "false").lower() == "true",
        "base_url": os.getenv("OPENAI_BASE_URL"),
        "organization": os.getenv("OPENAI_ORG_ID", None),
    }
