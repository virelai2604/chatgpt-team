import asyncio
import httpx
import os
import json
from datetime import datetime

# =========================================================
# CONFIGURATION
# =========================================================
BASE_URL = "https://chatgpt-team-relay.onrender.com/v1"
API_KEY = os.getenv("OPENAI_API_KEY") or "YOUR_API_KEY_HERE"
DOWNLOAD_DIR = r"C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\Downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# =========================================================
# PROGRESS BAR
# =========================================================
def progress_bar(progress: float, length: int = 30):
    """Simple progress bar for CLI output."""
    filled = int(length * progress / 100)
    bar = "=" * filled + "-" * (length - filled)
    return f"[{bar}] {progress:5.1f}%"


# =========================================================
# POLL /v1/responses/{id}
# =========================================================
async def poll_response_completion(client, response_id, interval=10, max_wait=5400):
    """Polls /v1/responses/{response_id} until status = completed or failed."""
    waited = 0
    print(f"⏳ Polling for video completion (max {max_wait // 60} min)...")

    while waited < max_wait:
        resp = await client.get(
            f"{BASE_URL}/responses/{response_id}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )

        if resp.status_code != 200:
            print(f"⚠️ Error polling: {resp.status_code} {resp.text}")
            await asyncio.sleep(interval)
            waited += interval
            continue

        data = resp.json()
        status = data.get("status", "unknown")
        print(f"Status: {status:<12}", end="\r")

        if status == "completed":
            print("\n✅ Video generation completed successfully.")
            return data
        elif status == "failed":
            print(f"\n❌ Video generation failed:\n{json.dumps(data, indent=2)}")
            raise RuntimeError("Video generation failed per API response.")
        else:
            await asyncio.sleep(interval)
            waited += interval

    raise TimeoutError(f"⚠️ Timeout: video not completed after {max_wait // 60} min.")


# =========================================================
# CREATE & DOWNLOAD VIDEO (Unified API)
# =========================================================
async def create_video(prompt: str, model="sora-2-pro", seconds=12):
    """
    Creates a cinematic video using /v1/responses (BIFL v2.1),
    polls until done, and downloads the resulting video.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-5",  # orchestrator model
        "input": f"Generate a {seconds}-second cinematic video: {prompt}",
        "tools": [
            {
                "type": "video_generation",
                "model": model,
                "seconds": seconds,
            }
        ]
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        print("🎬 Submitting video generation job (unified /v1/responses)...")
        response = await client.post(f"{BASE_URL}/responses", json=payload, headers=headers)
        data = response.json()

        if response.status_code != 200:
            raise RuntimeError(f"❌ Video creation failed: {data}")

        response_id = data["id"]
        print(f"🚀 Job created: {response_id}")

        # Poll until job completes
        job = await poll_response_completion(client, response_id)

        # Extract output info
        output = job.get("output", "")
        print(f"\n📦 Raw output:\n{json.dumps(output, indent=2)}")

        # Detect video file or URL
        file_id = None
        download_url = None

        # Handle if output is a JSON string
        if isinstance(output, str):
            try:
                output_data = json.loads(output)
            except json.JSONDecodeError:
                output_data = {"url": output}
        else:
            output_data = output

        # Check for file_id or URL fields
        if isinstance(output_data, dict):
            file_id = output_data.get("file_id") or output_data.get("id")
            download_url = output_data.get("url")

        # Attempt download from file_id first
        if file_id:
            print(f"⬇️ Downloading from file_id: {file_id}")
            content_resp = await client.get(
                f"{BASE_URL}/files/{file_id}/content",
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
            if content_resp.status_code == 200:
                filename = f"{DOWNLOAD_DIR}\\{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                with open(filename, "wb") as f:
                    f.write(content_resp.content)
                print(f"🎉 Saved video to:\n   {filename}")
                return filename
            else:
                print(f"⚠️ Download failed from file_id: {content_resp.text}")

        # Fallback: download from URL
        elif download_url:
            print(f"⬇️ Downloading from URL: {download_url}")
            content_resp = await client.get(download_url)
            if content_resp.status_code == 200:
                filename = f"{DOWNLOAD_DIR}\\video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                with open(filename, "wb") as f:
                    f.write(content_resp.content)
                print(f"🎉 Saved video to:\n   {filename}")
                return filename
            else:
                raise RuntimeError(f"❌ Download failed from URL: {download_url}")

        else:
            raise RuntimeError("❌ No valid video output (missing file_id or URL).")


# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    prompt = (
        "A majestic dragon flying over snow-covered mountains during golden hour, "
        "with an old-school epic instrumental soundtrack. "
        "Cinematic lighting, sweeping camera motion, fantasy atmosphere."
    )
    asyncio.run(create_video(prompt, model="sora-2-pro", seconds=12))
