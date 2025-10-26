# ==========================================================
# app/tools/embedding_tool.py — Text Embeddings
# ==========================================================
import os, httpx
from app.routes.services.tool_registry import register_tool

@register_tool("embedding_tool")
async def embedding_tool(text):
    """Generate embeddings for given text."""
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "text-embedding-3-large", "input": text}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
        return r.json()
