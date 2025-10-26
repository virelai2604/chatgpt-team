from app.routes.services.tool_registry import register_tool
import platform, os, datetime

@register_tool("system_tool")
async def system_tool():
    """Return system metadata and uptime."""
    return {
        "os": platform.system(),
        "version": platform.version(),
        "python": platform.python_version(),
        "relay_name": os.getenv("RELAY_NAME", "ChatGPT Team Relay"),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
