# app/routes/usage.py — BIFL v2.3.4-fp
from fastapi import APIRouter
from app.utils.db_logger import log_event

router = APIRouter(prefix="/v1/usage", tags=["Usage"])

@router.get("")
async def usage():
    await log_event("/v1/usage", 200, "usage-check")
    return {"ok": True}
