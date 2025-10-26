from app.routes.services.tool_registry import register_tool

@register_tool("retrieval_tool")
async def retrieval_tool(query: str):
    """Stub for retrieval using /v1/vector_stores."""
    return {"matches": [], "query": query}
