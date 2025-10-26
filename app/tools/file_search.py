# ==========================================================
# app/tools/file_search.py — Hybrid Vector File Search
# ==========================================================
import os, json, httpx
from app.routes.services.tool_registry import register_tool

@register_tool("file_search")
async def file_search(query: str):
    """Search uploaded files using embeddings."""
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Step 1: Embed query
    embed_payload = {"model": "text-embedding-3-large", "input": query}
    async with httpx.AsyncClient() as client:
        emb_res = await client.post("https://api.openai.com/v1/embeddings", headers=headers, json=embed_payload)
        embedding = emb_res.json()["data"][0]["embedding"]

        # Step 2: Retrieve matching file vectors
        vec_payload = {"query": embedding, "limit": 5}
        vec_res = await client.post("https://api.openai.com/v1/vector_stores/query", headers=headers, json=vec_payload)
        return vec_res.json()
