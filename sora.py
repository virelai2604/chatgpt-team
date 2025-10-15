import asyncio
import httpx
import os
import sys
import time

BASE_URL = "https://chatgpt-team-relay.onrender.com/v1"
DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Helper: progress bar ---
def progress_bar(progress: float, length: int = 30):
    filled = int(length * progress / 100)
    bar = "=" * filled + "-" * (length - filled)
    return f"[{bar}] {progress:.1f}%"

async def poll_video_completion(client, video_id, interval=10, max_wait=1800):
    """
    Polls /videos/{video_id} until status = completed or failed.
    Follows OpenAI's official polling guidance.
    """
    waited = 0
    while waited < max_wait:
        resp = await client.get(f"/videos/{video_id}")
        data = resp.json()
        status = data.get("status")
        progress = data.get("progress", 0)
        sys.stdout.write(f"\r{progress_bar(progress)} {status.upper()}   ")
        sys.stdout.flush()

        if status == "completed":
            print("\n✅ Video generation completed.")
            return data
        elif status == "failed":
            print("\n❌ Video generation failed.")
            raise Exception(data)

        await asyncio.sleep(interval)
        waited += interval
    raise TimeoutError(f"Timeout waiting for video job {video_id}")

async def download_video_content(client, video_id, filename, variant="video"):
    """
    Streams video (or thumbnail/spritesheet) content to disk.
    """
    print(f"⬇️  Downloading {variant} for {video_id} ...")
    async with client.stream("GET", f"/videos/{video_id}/content", params={"variant": variant}) as r:
        if r.status_code != 200:
            print(f"⚠️ Failed to download: {r.text}")
            return
        with open(filename, "wb") as f:
            async for chunk in r.aiter_bytes():
                f.write(chunk)
    print(f"✅ Saved to {filename}")

async def create_and_download_video(
    prompt: str,
    model: str = "sora-2-pro",
    seconds: str = "8",
    landscape: bool = True,
    remix_prompt: str | None = None,
):
    """
    Generic, reusable Sora 2 / Sora 2 Pro generation workflow.
    Supports remix and optional landscape orientation prompting.
    """
    # Append cinematic orientation hint
    if landscape:
        prompt += (
            " Render as a cinematic widescreen landscape film in 16:9 aspect ratio (1920x1080 preferred). "
            "Do not make it portrait. Movie-quality horizontal framing, full width."
        )

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=900) as client:
        # 1️⃣ Create video
        payload = {"model": model, "prompt": prompt, "seconds": seconds}
        print(f"🎬 Creating {model} job...")
        resp = await client.post("/videos", json=payload)
        assert resp.status_code == 200, f"❌ Creation failed: {resp.text}"
        video_id = resp.json()["id"]
        print(f"🆔 Job ID: {video_id}")

        # 2️⃣ Poll until complete
        video_data = await poll_video_completion(client, video_id)

        # 3️⃣ Download main video
        video_path = os.path.join(DOWNLOAD_DIR, f"{video_id}_{model}_{seconds}s.mp4")
        await download_video_content(client, video_id, video_path, variant="video")

        # 4️⃣ Optional thumbnail or spritesheet
        thumb_path = os.path.join(DOWNLOAD_DIR, f"{video_id}_thumbnail.webp")
        await download_video_content(client, video_id, thumb_path, variant="thumbnail")

        # 5️⃣ Remix (optional)
        if remix_prompt:
            print(f"\n🎨 Remixing video {video_id} ...")
            remix_resp = await client.post(f"/videos/{video_id}/remix", json={"prompt": remix_prompt})
            assert remix_resp.status_code == 200, f"❌ Remix failed: {remix_resp.text}"
            remix_id = remix_resp.json()["id"]
            print(f"🆕 Remix ID: {remix_id}")
            remix_data = await poll_video_completion(client, remix_id)
            remix_path = os.path.join(DOWNLOAD_DIR, f"{remix_id}_{model}_{seconds}s_remix.mp4")
            await download_video_content(client, remix_id, remix_path, variant="video")

        print("\n✅ All tasks completed successfully.")

if __name__ == "__main__":
    # --- Customize your creative scene ---
    prompt = (
        "Cinematic hero trailer — a frostbitten man stands on a snowy cliff as alien warships roar overhead, "
        "explosions lighting up the frozen peaks. Slow-motion zoom on his determined eyes, frost clinging to his beard, "
        "looking at burning temple. Title flashes: 'HERO.' Epic heroic orchestral music swells. "
        "Cold color grade, cinematic realism."
    )
    remix_prompt = "Remix: Transform the setting to a glowing sunrise illuminating the peaks with golden light."

    asyncio.run(
        create_and_download_video(
            prompt=prompt,
            model="sora-2-pro",
            seconds="12",
            landscape=True,
            remix_prompt=remix_prompt,
        )
    )
