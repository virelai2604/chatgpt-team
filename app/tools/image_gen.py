from app.routes.services.tool_registry import register_tool
import os, httpx

@register_tool("image_gen")
async def image_gen(prompt: str, size: str = "1024x1024"):
    """Generate or edit an image using gpt-image-1 (DALL·E 3)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "Missing OPENAI_API_KEY"}
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": "gpt-image-1", "prompt": prompt, "size": size}
    async with httpx.AsyncClient() as client:
        r = await client.post("https://api.openai.com/v1/images/generations", headers=headers, json=payload)
        return r.json()
