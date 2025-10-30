from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os

router = APIRouter(tags=["Core"])

@router.get("/health")
async def health():
    return {"status": "ok", "version": os.getenv("BIFL_VERSION", "v2.3.4-fp")}


@router.get("/")
async def root():
    return {
        "service": "ChatGPT Team Relay",
        "status": "running",
        "version": os.getenv("BUILD_DATE", "unknown"),
        "chain_wait_mode": os.getenv("CHAIN_WAIT_MODE", "false"),
        "docs": "/docs",
        "openapi_spec": "/v1/openapi.yaml",
    }
