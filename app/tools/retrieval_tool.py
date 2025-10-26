# ==========================================================
# app/tools/retrieval_tool.py — Contextual Retrieval
# ==========================================================
import os, httpx
from app.routes.services.tool_registry import register_tool

@register_tool("retrieval_tool")
async def retrieval_tool(query: str):
    """Retrieve relevant context chunks from vector store."""
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "text-embedding-3-large", "input": query}

    async with httpx.AsyncClient() as client:
        emb = await client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
        emb_vec = emb.json()["data"][0]["embedding"]
        retrieve = await client.post("https://api.openai.com/v1/vector_stores/query", headers=headers, json={"query": emb_vec})
        return retrieve.json()
