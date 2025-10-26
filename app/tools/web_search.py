from app.routes.services.tool_registry import register_tool
import os, httpx

@register_tool("web_search")
async def web_search(query: str):
    """Search the web for up-to-date information."""
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return {"error": "Missing TAVILY_API_KEY"}
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://api.tavily.com/search",
                                 json={"query": query, "api_key": key})
        return resp.json()
