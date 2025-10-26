# app/routes/services/tools_admin.py — BIFL v2.3.4-fp
import os
from fastapi import APIRouter

router = APIRouter(prefix="/v1/tools/admin", tags=["Tools Admin"])

@router.get("/version")
async def version():
    return {
        "bifl_version": "2.3.4-fp",
        "build_date": os.getenv("BUILD_DATE", "unknown"),
        "build_channel": os.getenv("BUILD_CHANNEL", "stable"),
        "auto_load_builtins": os.getenv("AUTOLOAD_BUILTIN_TOOLS", "true"),
    }

@router.get("/reload")
async def reload_tools():
    return {"message": "Tool reload not required (static registry)."}
