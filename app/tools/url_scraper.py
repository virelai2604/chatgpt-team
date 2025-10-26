from app.routes.services.tool_registry import register_tool
import httpx

@register_tool("url_scraper")
async def url_scraper(url: str):
    """Fetch and summarize webpage content."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            content = r.text[:2000]  # Limit output for safety
        return {"url": url, "content_snippet": content}
    except Exception as e:
        return {"error": str(e)}
