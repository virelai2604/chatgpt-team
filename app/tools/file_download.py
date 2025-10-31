"""
app/tools/file_download.py
Downloads a file from a given URL and returns metadata.
"""

import httpx
import asyncio
from tempfile import NamedTemporaryFile

async def download_file(params: dict):
    url = params.get("url")
    if not url:
        return {"error": "Missing 'url' parameter."}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return {"error": f"Failed to download ({resp.status_code})."}

        with NamedTemporaryFile(delete=False) as tmp:
            tmp.write(resp.content)
            path = tmp.name

    await asyncio.sleep(0.1)
    return {"url": url, "saved_path": path, "size_bytes": len(resp.content)}
