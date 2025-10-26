from app.routes.services.tool_registry import register_tool

@register_tool("echo_tool")
async def echo_tool(text: str):
    """Echoes input for debugging."""
    return {"echo": text}
