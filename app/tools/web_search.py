# ============================================================
# Tool: web_search — Mock search provider
# ============================================================

TOOL_SCHEMA = {
    "name": "web_search",
    "description": "Perform a real-time web search and return the top results.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "default": 5}
        },
        "required": ["query"]
    },
    "returns": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "url": {"type": "string"}, "snippet": {"type": "string"}}
        }
    }
}

async def run(payload: dict) -> list:
    """Returns mock search results."""
    query = payload.get("query", "")
    n = int(payload.get("max_results", 5))
    return [{"title": f"Result {i+1}", "url": f"https://example.com/{i}", "snippet": f"Mock snippet for '{query}'"} for i in range(n)]
