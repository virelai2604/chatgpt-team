# app/routes/services/tool_registry.py
import json
from typing import Any, Dict, List, Callable, Awaitable, Union

# Example local tool (replace with real integrations)
async def get_current_weather(location: str, unit: str) -> Dict[str, Any]:
    # TODO: Plug in your provider here (OpenWeather, internal weather svc, etc.)
    return {"location": location, "unit": unit, "temp": 18, "conditions": "cloudy"}

# Name -> async function
REGISTRY: Dict[str, Callable[..., Awaitable[Any]]] = {
    "get_current_weather": get_current_weather,
}

async def execute_function_call_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a function_call output item -> tool_result input item.
    Safely parses JSON args and invokes the registered function by name.
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
        # Return a structured error result; the model can recover gracefully
        return {
            "type": "tool_result",
            "tool_name": name or "unknown_tool",
            "call_id": call_id,
            "output": {"error": f"unregistered tool '{name}'"}
        }
    # Execute the tool
    result = await fn(**args)
    return {
        "type": "tool_result",
        "tool_name": name,
        "call_id": call_id,
        "output": result
    }

async def collect_tool_results(response_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scans `output[]` for function calls; executes those we know locally.
    Returns a list of tool_result input items to feed back to /v1/responses.
    """
    tool_results: List[Dict[str, Any]] = []
    for out in response_json.get("output", []):
        if out.get("type") == "function_call":
            tool_results.append(await execute_function_call_item(out))
    return tool_results
# app/routes/services/tool_registry.py
import json
from typing import Any, Dict, List, Callable, Awaitable, Union

# Example local tool (replace with real integrations)
async def get_current_weather(location: str, unit: str) -> Dict[str, Any]:
    # TODO: Plug in your provider here (OpenWeather, internal weather svc, etc.)
    return {"location": location, "unit": unit, "temp": 18, "conditions": "cloudy"}

# Name -> async function
REGISTRY: Dict[str, Callable[..., Awaitable[Any]]] = {
    "get_current_weather": get_current_weather,
}

async def execute_function_call_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a function_call output item -> tool_result input item.
    Safely parses JSON args and invokes the registered function by name.
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
        # Return a structured error result; the model can recover gracefully
        return {
            "type": "tool_result",
            "tool_name": name or "unknown_tool",
            "call_id": call_id,
            "output": {"error": f"unregistered tool '{name}'"}
        }
    # Execute the tool
    result = await fn(**args)
    return {
        "type": "tool_result",
        "tool_name": name,
        "call_id": call_id,
        "output": result
    }

async def collect_tool_results(response_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scans `output[]` for function calls; executes those we know locally.
    Returns a list of tool_result input items to feed back to /v1/responses.
    """
    tool_results: List[Dict[str, Any]] = []
    for out in response_json.get("output", []):
        if out.get("type") == "function_call":
            tool_results.append(await execute_function_call_item(out))
    return tool_results
