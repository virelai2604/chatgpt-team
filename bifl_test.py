import os, time, json, requests, pytest
from datetime import datetime

# === CONFIG ===
API_BASE = "https://chatgpt-team-relay.onrender.com/v1"
API_KEY = os.getenv("BIFL_API_KEY", "sk-test")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
DOWNLOADS = r"C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\Downloads"
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "BIFL_Checklist_Report.md")

# === STATE ===
checklist = {}

# === UTILS ===
def write_md_report():
    with open(DESKTOP_PATH, "w", encoding="utf-8") as f:
        f.write(f"# 🧩 BIFL Auto Checklist Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Endpoint | Method | Status | Notes |\n")
        f.write("|-----------|---------|---------|--------|\n")
        for ep, data in checklist.items():
            f.write(f"| {ep} | {data['method']} | {data['status']} | {data['note']} |\n")

def update_checklist(endpoint, method, status, note=""):
    checklist[endpoint] = {"method": method, "status": status, "note": note}
    print(f"\n📋 {endpoint} [{method}] → {status} {note}")
    write_md_report()

def request_with_retry(method, path, **kwargs):
    url = f"{API_BASE}{path}"
    r = requests.request(method, url, headers=HEADERS, **kwargs)
    if r.status_code >= 400:
        headers_v2 = dict(HEADERS)
        headers_v2["OpenAI-Beta"] = "assistants=v2"
        r = requests.request(method, url, headers=headers_v2, **kwargs)
    return r

# === VIDEO FUNCTIONS ===
def poll_video(video_id, timeout=240):
    for _ in range(timeout // 5):
        r = requests.get(f"{API_BASE}/videos/{video_id}", headers=HEADERS)
        if r.ok and r.json().get("status") == "completed":
            return True
        time.sleep(5)
    return False

def download_video(video_id, prefix=""):
    r = requests.get(f"{API_BASE}/videos/{video_id}/content", headers=HEADERS)
    fpath = os.path.join(DOWNLOADS, f"{prefix}{video_id}.mp4")
    if r.ok:
        with open(fpath, "wb") as f:
            f.write(r.content)
        print(f"💾 Saved video: {fpath}")
        return True
    print(f"⚠️ Download failed for {video_id}: {r.status_code}")
    return False

def test_videos(model, prompt, prefix):
    ep = f"/videos ({model})"
    payload = {"prompt": prompt, "seconds": "4", "model": model}
    r = request_with_retry("POST", "/videos", json=payload)
    if not r.ok:
        update_checklist(ep, "POST", "❌ FAIL", f"create {r.status_code}")
        return
    vid = r.json().get("id")
    if not poll_video(vid):
        update_checklist(ep, "POST", "❌ FAIL", "timeout")
        return
    if not download_video(vid, prefix):
        update_checklist(ep, "GET", "❌ FAIL", "download error")
        return
    # Remix
    remix = request_with_retry("POST", f"/videos/{vid}/remix",
        json={"prompt": "same scene but cinematic, warm tone"})
    if not remix.ok:
        update_checklist(ep, "POST", "❌ FAIL", f"remix {remix.status_code}")
        return
    remix_id = remix.json().get("id")
    if not poll_video(remix_id):
        update_checklist(ep, "POST", "❌ FAIL", "remix timeout")
        return
    if not download_video(remix_id, prefix + "REMIX_"):
        update_checklist(ep, "GET", "❌ FAIL", "remix download")
        return
    update_checklist(ep, "POST", "✅ PASS")

# === GENERIC ENDPOINT TEST ===
def test_generic(method, endpoint, json_data=None):
    path = endpoint.replace("{video_id}", "video_68ed0c9a0e48819099f64f6a8eb612c00875fdc385853e5d") \
                   .replace("{assistant_id}", "asst_123") \
                   .replace("{thread_id}", "thread_123") \
                   .replace("{message_id}", "msg_123") \
                   .replace("{run_id}", "run_123")
    r = request_with_retry(method, path, json=json_data)
    if r.ok:
        update_checklist(endpoint, method, "✅ PASS")
    else:
        update_checklist(endpoint, method, "❌ FAIL", f"{r.status_code}")

# === MAIN ===
if __name__ == "__main__":
    print("🚀 Starting full BIFL Auto Checklist Test Run...")
    os.makedirs(DOWNLOADS, exist_ok=True)

    # VIDEO TESTS FIRST (so we have valid IDs)
    test_videos("sora-2", "sunshine over a lake", "SUN_")
    test_videos("sora-2-pro", "sunshine over a lake", "MOON_")

    # ENDPOINTS
    endpoints = [
        ("POST", "/chat/completions", {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}),
        ("POST", "/embeddings", {"model": "text-embedding-3-small", "input": "testing embedding"}),
        ("GET", "/files", None),
        ("GET", "/models", None),
        ("POST", "/assistants", {"model": "gpt-4o-mini", "name": "autotest"}),
        ("POST", "/threads", None),
        ("GET", "/vector_stores", None),
        ("POST", "/vector_stores", {"name": "demo_store"}),
        ("GET", "/tools", None),
        ("POST", "/tools", {"name": "testtool"})
    ]

    for method, ep, data in endpoints:
        test_generic(method, ep, data)

    print("\n✅ All endpoints tested.")
    write_md_report()
    print(f"\n📄 Report saved to: {DESKTOP_PATH}")
