"""
app/tools/web_search.py
Performs live web search via DuckDuckGo or fallback mock results.
"""

import httpx
import asyncio

async def perform_search(params: dict):
    query = params.get("query", "")
    if not query:
        return {"error": "Missing 'query' parameter."}

    # Use DuckDuckGo API (no API key needed)
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            related = data.get("RelatedTopics", [])
            results = [t.get("Text", "") for t in related if t.get("Text")]
            return {"query": query, "results": results[:5]}

    await asyncio.sleep(0.1)
    return {"query": query, "results": ["No results found."]}
