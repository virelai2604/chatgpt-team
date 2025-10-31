"""
app/tools/file_upload.py
Uploads a local file to OpenAI-compatible file storage or a mock system.
"""

import os
import httpx
import asyncio

async def upload_file(params: dict):
    filepath = params.get("filepath")
    purpose = params.get("purpose", "assistants")
    openai_url = params.get("openai_url", "https://api.openai.com/v1/files")

    if not filepath or not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}

    with open(filepath, "rb") as f:
        files = {"file": (os.path.basename(filepath), f, "application/octet-stream")}
        data = {"purpose": purpose}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(openai_url, data=data, files=files)

    await asyncio.sleep(0.1)
    return {"filepath": filepath, "status": resp.status_code, "response": resp.text}
