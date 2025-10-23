# app/routes/services/tool_router.py
# Optional helper for alternative flow; kept for backward-compat imports.
import json
from typing import Dict, List, Any
from .tool_registry import REGISTRY

async def maybe_execute_function_calls(response_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find function_call outputs and return a list of tool_result items."""
    tool_results: List[Dict[str, Any]] = []
    for out in response_json.get("output", []):
        if out.get("type") == "function_call":
            name = out["name"]
            fn = REGISTRY.get(name)
            if fn:
                args = out.get("arguments", "{}")
                args = json.loads(args) if isinstance(args, str) else (args or {})
                result = await fn(**args)
                tool_results.append({
                    "type": "tool_result",
                    "tool_name": name,
                    "call_id": out.get("call_id") or out.get("id") or "call_0",
                    "output": result
                })
            else:
                tool_results.append({
                    "type": "tool_result",
                    "tool_name": name,
                    "call_id": out.get("call_id") or out.get("id") or "call_0",
                    "output": {"error": f"unregistered tool '{name}'"}
                })
    return tool_results
