"""
app/tools/image_generation.py
Generates or simulates image creation via prompt input.
"""

import os
import httpx
import asyncio

async def generate_image(params: dict):
    prompt = params.get("prompt", "")
    model = params.get("model", "gpt-image-1")

    # Try forwarding to OpenAI if API key exists
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "prompt": prompt},
            )
            if resp.status_code == 200:
                data = resp.json()
                return {"model": model, "prompt": prompt, "image": data.get("data", [{}])[0]}
            return {"error": f"API error {resp.status_code}"}

    # Offline fallback
    await asyncio.sleep(0.1)
    return {"url": f"https://dummyimage.com/600x400/000/fff&text={prompt.replace(' ', '+')}"}
