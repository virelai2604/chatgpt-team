import asyncio
import httpx
import os
import sys
import re
import json
from datetime import datetime

# =========================================================
# CONFIGURATION
# =========================================================
BASE_URL = "https://chatgpt-team-relay.onrender.com/v1"
DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Adjustable Input Parameters (Reference) ---
# model:        "sora-2" | "sora-2-pro"
# seconds:      "4" | "8" | "12"  ← default = "12"
# landscape:    True = cinematic 16:9 (1920x1080, max res)
# remix_prompt: optional second-generation variation
# soraPrompt parameters:
#   cameraType:   "static" | "handheld" | "drone" | "dolly" | "steadycam" | "zoom"
#   lighting:     "natural light" | "studio light" | "sunset" | "neon" | "soft" | "harsh"
#   visualMood:   "tranquil" | "cinematic" | "dramatic" | "ethereal" | "documentary"
#   environment:  "urban" | "tropical" | "interior" | "mountain" | "forest" | "industrial"
#   narrativeTone:"architectural showcase" | "heroic" | "romantic" | "mysterious" | "inspirational"

# =========================================================
# PROGRESS BAR + POLLING
# =========================================================
def progress_bar(progress: float, length: int = 30):
    filled = int(length * progress / 100)
    bar = "=" * filled + "-" * (length - filled)
    return f"[{bar}] {progress:5.1f}%"

async def poll_video_completion(client, video_id, interval=10, max_wait=5400):
    """
    Polls /videos/{video_id} until status = completed or failed.
    5400 s = 90 min max wait for long 12 s renders.
    """
    waited = 0
    print(f"⏳ Polling for video completion (max {max_wait/_
