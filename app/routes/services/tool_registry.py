# app/routes/services/tool_registry.py
"""
BIFL v2.1 – Local Tool Registry with Parallel Execution & Dynamic Loading
Supports:
1. Async parallel execution of multiple function_call outputs.
2. Dynamic registry loading from config/tools.json.
"""

import os
import json
import asyncio
import importlib
from typing import Any, Dict, List, Callable, Awaitable

# ───────────────────────────────────────────────────────────────
#  Example Local Tool
#  (You can override or add new ones in config/tools.json)
# ───────────────────────────────────────────────────────────────
async def get_current_weather(location: str, unit: str = "C") -> Dict[str, Any]:
    """Simple built-in example tool."""
    return {
        "location": location,
        "unit": unit,
        "temp": 27 if unit.upper().startswith("C") else 80.6,
        "conditions": "clear",
    }

# ───────────────────────────────────────────────────────────────
#  Registry Initialization
# ───────────────────────────────────────────────────────────────
REGISTRY: Dict[str, Callable[..., Awaitable[Any]]] = {
    "get_current_weather": get_current_weather,
}

TOOLS_CONFIG = os.getenv("TOOLS_CONFIG", "config/tools.json")

if os.path.exists(TOOLS_CONFIG):
    try:
        with open(TOOLS_CONFIG, "r", encoding="utf-8") as f:
            tool_defs = json.load(f)
        for name, path in tool_defs.items():
            module_name, fn_name = path.rsplit(".", 1)
            mod = importlib.import_module(module_name)
            REGISTRY[name] = getattr(mod, fn_name)
        print(f"[tool_registry] Loaded {len(tool_defs)} tools from {TOOLS_CONFIG}")
    except Exception as e:
        print(f"[tool_registry] Error loading tools from {TOOLS_CONFIG}: {e}")

# ───────────────────────────────────────────────────────────────
#  Function Execution Logic
# ───────────────────────────────────────────────────────────────
async def execute_function_call_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute one function_call item from a /v1/responses payload.
    """
    name = item.get("name")
    call_id = item.get("call_id") or item.get("id") or "call_0"
    args_raw = item.get("arguments") or "{}"

    try:
        args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
    except Exception:
        args = {}

    fn = REGISTRY.get(name)
    if not fn:
        return {
            "type": "tool_result",
            "tool_name": name or "unknown_tool",
            "call_id": call_id,
            "output": {"error": f"unregistered tool '{name}'"},
        }

    try:
        result = await fn(**args)
    except Exception as ex:
        result = {"error": str(ex)}

    return {
        "type": "tool_result",
        "tool_name": name,
        "call_id": call_id,
        "output": result,
    }

# ───────────────────────────────────────────────────────────────
#  Parallel Tool Result Collector
# ───────────────────────────────────────────────────────────────
async def collect_tool_results(response_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Execute all function_call items concurrently using asyncio.gather().
    """
    calls = [
        o for o in response_json.get("output", [])
        if o.get("type") == "function_call"
    ]
    if not calls:
        return []
    results = await asyncio.gather(*(execute_function_call_item(c) for c in calls))
    return list(results)
