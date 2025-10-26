from app.routes.services.tool_registry import register_tool
import math

@register_tool("code_interpreter")
async def code_interpreter(code: str):
    """Safely evaluate small Python snippets."""
    try:
        return {"output": eval(code, {"math": math, "__builtins__": {}})}
    except Exception as e:
        return {"error": str(e)}
