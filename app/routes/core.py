# app/routes/core.py — BIFL v2.3.4-fp
from fastapi import APIRouter

router = APIRouter(prefix="/v1/core", tags=["Core"])

@router.get("/ping")
async def ping():
    return {"pong": True}
