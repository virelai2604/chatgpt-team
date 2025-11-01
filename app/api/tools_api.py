"""
tools_api.py — Ground Truth API v1.7
Executes tools from tools_manifest.json for /v1/responses.
"""

import importlib
import json
import asyncio
import traceback
import time
from functools import lru_cache
from typing import Any, Dict, Callable
from fastapi import HTTPException
from app.utils.logger import logger

MANIFEST_PATH = "app/manifests/tools_manifest.json"


@lru_cache(maxsize=1)
def load_tools_manifest() -> Dict[str, Any]:
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        tools = {t["tool_name"]: t for t in manifest.get("tools", [])
                 if t.get("enabled")}
        logger.info(f"Loaded {len(tools)} enabled tools from manifest.")
        return tools
    except Exception as e:
        logger.error(f"Failed to load tools manifest: {e}")
        raise HTTPException(status_code=500, detail="Error loading tools manifest")


async def execute_tool_from_manifest(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    tools = load_tools_manifest()
    tool = tools.get(tool_name)
    if not tool:
        return {
            "tool": tool_name,
            "status": "error",
            "error_type": "NotFound",
            "message": f"Tool '{tool_name}' not found or disabled."
        }

    entrypoint = tool.get("entrypoint")
    try:
        module_name, func_name = entrypoint.rsplit(".", 1)
        module = importlib.import_module(module_name)
        func: Callable[..., Any] = getattr(module, func_name)
    except Exception as e:
        logger.error(f"Invalid entrypoint for {tool_name}: {e}")
        return {
            "tool": tool_name,
            "status": "error",
            "error_type": "ImportError",
            "message": str(e)
        }

    start = time.perf_counter()
    try:
        result = await asyncio.wait_for(_maybe_await(func, **args), timeout=30)
        elapsed = round(time.perf_counter() - start, 3)
        logger.info(f"Tool '{tool_name}' executed in {elapsed}s")
        return {"tool": tool_name, "status": "success",
                "duration": elapsed, "output": result}
    except asyncio.TimeoutError:
        msg = f"Tool '{tool_name}' timed out."
        logger.warning(msg)
        return {"tool": tool_name, "status": "error",
                "error_type": "TimeoutError", "message": msg}
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Tool '{tool_name}' failed: {e}\n{tb}")
        return {"tool": tool_name, "status": "error",
                "error_type": type(e).__name__, "message": str(e)}


async def _maybe_await(func: Callable, **kwargs):
    if asyncio.iscoroutinefunction(func):
        return await func(**kwargs)
    return func(**kwargs)
