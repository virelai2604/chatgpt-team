# app/routes/relay_status.py
# BIFL v2.2 — Unified Relay Status & Health Check
# Provides system diagnostics, uptime, route status, and latency monitoring.

import os
import time
import platform
import psutil
import aiohttp
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.api.forward import forward_openai


router = APIRouter(prefix="/v1/relay", tags=["Relay Status"])

START_TIME = time.time()
VERSION = "v2.2"
RELAY_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
ENDPOINTS = [
    "/v1/models",
    "/v1/responses",
    "/v1/files",
    "/v1/vector_stores",
    "/v1/audio/transcriptions",
]


async def check_endpoint(url: str) -> dict:
    """Ping internal or upstream endpoint and measure latency."""
    start = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                status = resp.status
        latency = round((time.time() - start) * 1000, 2)
        return {"url": url, "status": status, "latency_ms": latency}
    except Exception as e:
        latency = round((time.time() - start) * 1000, 2)
        return {"url": url, "status": "error", "error": str(e), "latency_ms": latency}


def system_metrics() -> dict:
    """Gather system resource usage metrics."""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime = time.time() - START_TIME
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": mem.percent,
        "disk_percent": disk.percent,
        "uptime_sec": round(uptime, 2),
        "uptime_human": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
    }


@router.get("/status")
async def get_relay_status():
    """Return relay health, metrics, and endpoint availability."""
    metrics = system_metrics()
    base_url = os.getenv("RELAY_BASE", "https://chatgpt-team-relay.onrender.com")
    endpoint_results = await asyncio.gather(*[check_endpoint(base_url + e) for e in ENDPOINTS])

    healthy_count = sum(1 for r in endpoint_results if r.get("status") == 200)
    status = "healthy" if healthy_count >= len(ENDPOINTS) - 1 else "degraded"

    return JSONResponse(content={
        "object": "relay_status",
        "relay_name": RELAY_NAME,
        "version": VERSION,
        "system": platform.system(),
        "status": status,
        "metrics": metrics,
        "endpoints": endpoint_results,
        "models_available": await list_models_safe(),
        "timestamp": int(time.time()),
    })


async def list_models_safe():
    """Try fetching model list, fallback to cached/empty."""
    try:
        models = await forward_openai(path="/v1/models", method="GET")
        return models.get("data", []) if isinstance(models, dict) else []
    except Exception:
        return [{"id": "unknown", "object": "model", "note": "relay offline"}]


@router.get("/ping")
async def ping():
    """Simple relay heartbeat check."""
    return JSONResponse(content={
        "object": "ping",
        "status": "ok",
        "version": VERSION,
        "uptime": system_metrics()["uptime_human"],
        "time": int(time.time()),
    })


@router.get("/debug")
async def relay_debug():
    """Extended debug info for system state."""
    info = {
        "object": "relay_debug",
        "system": {
            "platform": platform.system(),
            "release": platform.release(),
            "python": platform.python_version(),
        },
        "metrics": system_metrics(),
        "env": {
            "RELAY_NAME": RELAY_NAME,
            "BASE_URL": os.getenv("RELAY_BASE", "N/A"),
            "MODE": os.getenv("ENVIRONMENT", "development"),
        },
        "version": VERSION,
        "timestamp": int(time.time()),
    }
    return JSONResponse(content=info)
