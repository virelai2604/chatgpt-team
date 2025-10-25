"""
BIFL helper – lightweight wrapper for optional direct tool execution.
Keeps backward compatibility with older imports expecting tool_router.
"""
import json
from typing import Dict, List, Any
from .tool_registry import REGISTRY

async def maybe_execute_function_calls(response_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fallback executor: detect function_call items in a response,
    run local tools if registered, and produce tool_result objects.
    """
    tool_results: List[Dict[str, Any]] = []
    for out in response_json.get("output", []):
        if out.get("type") != "function_call":
            continue

        name = out.get("name")
        fn = REGISTRY.get(name)
        args = out.get("arguments", "{}")
        try:
            args = json.loads(args) if isinstance(args, str) else (args or {})
        except Exception:
            args = {}

        if not fn:
            tool_results.append({
                "type": "tool_result",
                "tool_name": name,
                "call_id": out.get("call_id") or out.get("id") or "call_0",
                "output": {"error": f"unregistered tool '{name}'"},
            })
            continue

        try:
            result = await fn(**args)
        except Exception as ex:
            result = {"error": str(ex)}

        tool_results.append({
            "type": "tool_result",
            "tool_name": name,
            "call_id": out.get("call_id") or out.get("id") or "call_0",
            "output": result,
        })
    return tool_results
