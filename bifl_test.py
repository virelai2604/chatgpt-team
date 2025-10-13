import os
import requests
import json
import time

SAMPLES = r"C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\samples files"
RELAY = "https://chatgpt-team-relay.onrender.com/v1"
API_KEY = "None"  # Add if needed; else, set to None

def auth_headers():
    if not API_KEY or "sk-" not in API_KEY:
        return {}
    return {"Authorization": f"Bearer {API_KEY}"}

def post_file(endpoint, filename, field="file"):
    path = os.path.join(SAMPLES, filename)
    with open(path, "rb") as f:
        files = {field: (filename, f)}
        r = requests.post(RELAY + endpoint, files=files, headers=auth_headers())
    print(f"Upload to {endpoint}: {r.status_code}")
    try:
        return r.json()
    except Exception:
        return {}

def download_and_save(endpoint, outname):
    r = requests.get(RELAY + endpoint, headers=auth_headers(), stream=True)
    print(f"Download {endpoint}: {r.status_code}")
    if r.status_code == 200:
        path = os.path.join(SAMPLES, outname)
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Saved to {path}")
        return path
    print(f"❌ Download failed for {endpoint}")
    return None

def main():
    # Test /files upload/list
    for fname in ["sample.txt", "sample.json", "sample.png", "sample.pdf", "sample.csv", "sample.mp3"]:
        post_file("/files", fname)
    requests.get(RELAY + "/files", headers=auth_headers())

    # Test /attachments upload/list/download
    att = post_file("/attachments/upload", "sample.json")
    chat_id = att.get("chat_id")
    if chat_id:
        download_and_save(f"/attachments/{chat_id}/download", f"download_{chat_id}.json")
    requests.get(RELAY + "/attachments/list", headers=auth_headers())

    # Test /images/generations
    img_req = {
        "model": "dall-e-3",
        "prompt": "A robot painting at sunset.",
        "n": 1
    }
    r = requests.post(RELAY + "/images/generations", json=img_req, headers=auth_headers())
    if r.ok:
        img_info = r.json()
        # If your relay returns IDs:
        if "data" in img_info and img_info["data"]:
            image_id = img_info["data"][0].get("id") or img_info["data"][0].get("image_id")
            if image_id:
                download_and_save(f"/images/{image_id}/content", f"dalle_{image_id}.png")

    # /audio/speech (TTS)
    tts_req = {"model": "tts-1", "input": "This is a BIFL relay audio test."}
    tts_r = requests.post(RELAY + "/audio/speech", json=tts_req, headers=auth_headers())
    if tts_r.ok:
        with open(os.path.join(SAMPLES, "sample_tts.mp3"), "wb") as f:
            f.write(tts_r.content)
        print(f"✅ Saved TTS MP3 to {os.path.join(SAMPLES, 'sample_tts.mp3')}")

    # /videos (Sora)
    v = requests.post(RELAY + "/videos", json={
        "prompt": "A panda riding a motorcycle through the city, cinematic.",
        "model": "sora-1"
    }, headers=auth_headers())
    if v.ok:
        vid = v.json()
        vid_id = vid.get("id") or vid.get("video_id")
        if vid_id:
            print(f"Polling video status for {vid_id}...")
            for _ in range(20):
                s = requests.get(RELAY + f"/videos/{vid_id}", headers=auth_headers())
                status = s.json().get("status", "")
                if status == "succeeded":
                    download_and_save(f"/videos/{vid_id}/content", "sample_sora_video.mp4")
                    break
                elif status == "failed":
                    print("Video generation failed.")
                    break
                time.sleep(10)

    print("\n✅ All BIFL endpoints tested. Check your samples folder!")

if __name__ == "__main__":
    main()
