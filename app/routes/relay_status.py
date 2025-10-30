from fastapi import APIRouter
import os
import platform
import time

router = APIRouter(prefix="/v1/status", tags=["Status"])

start_time = time.time()

@router.get("")
async def status():
    uptime = round(time.time() - start_time, 2)
    return {
        "relay": os.getenv("RELAY_NAME", "ChatGPT Team Relay"),
        "version": os.getenv("BIFL_VERSION", "v2.3.4-fp"),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "uptime": f"{uptime}s",
        "platform": platform.system(),
        "build_date": os.getenv("BUILD_DATE", "unknown")
    }
