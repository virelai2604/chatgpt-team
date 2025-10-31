"""
app/tools/video_generation.py
Simulates video generation based on prompt and model.
"""

import asyncio

async def generate_video(params: dict):
    prompt = params.get("prompt", "")
    model = params.get("model", "sora-2-pro")
    duration = int(params.get("seconds", 3))

    await asyncio.sleep(0.2)
    return {
        "model": model,
        "prompt": prompt,
        "duration_s": duration,
        "video_url": f"https://fakevideo.ai/render?model={model}&prompt={prompt.replace(' ', '+')}&dur={duration}",
    }
