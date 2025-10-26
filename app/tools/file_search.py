from app.routes.services.tool_registry import register_tool

@register_tool("file_search")
async def file_search(query: str):
    """Search within local files or vector stores."""
    return {"results": [], "query": query}
