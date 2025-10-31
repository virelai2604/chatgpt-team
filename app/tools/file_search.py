"""
app/tools/file_search.py
Searches text content in a directory or list of files.
"""

import os
import asyncio

async def search_files(params: dict):
    query = params.get("query", "")
    directory = params.get("directory", ".")
    if not query:
        return {"error": "Missing search query."}

    results = []
    for root, _, files in os.walk(directory):
        for f in files:
            try:
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                    if query.lower() in content.lower():
                        results.append(path)
            except Exception:
                continue

    await asyncio.sleep(0.1)
    return {"query": query, "matches": results[:50]}
