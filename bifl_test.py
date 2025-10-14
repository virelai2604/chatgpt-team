import os
import time
import requests
import pytest

API_BASE = "https://chatgpt-team-relay.onrender.com/v1"
HEADERS = {}  # No Authorization; relay does this
HEADERS_V2 = {**HEADERS, "OpenAI-Beta": "assistants=v2"}

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
SAMPLES = r"C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\samples files"
DOWNLOADS = r"C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\Downloads"

AUDIO_MP3 = os.path.join(SAMPLES, "bifl_test_audio.mp3")
UPLOAD_JSONL = os.path.join(SAMPLES, "test_upload.jsonl")

CHECKLIST = [
    {"name": "chatCompletions", "method": "POST", "path": "/v1/chat/completions"},
    {"name": "createEmbedding", "method": "POST", "path": "/v1/embeddings"},
    {"name": "listFiles", "method": "GET", "path": "/v1/files"},
    {"name": "uploadFile", "method": "POST", "path": "/v1/files"},
    {"name": "getFile", "method": "GET", "path": "/v1/files/{file_id}"},
    {"name": "deleteFile", "method": "DELETE", "path": "/v1/files/{file_id}"},
    {"name": "generateImage", "method": "POST", "path": "/v1/images/generations"},
    {"name": "getImageContent", "method": "GET", "path": "/v1/images/{image_id}/content"},
    {"name": "audioSpeech", "method": "POST", "path": "/v1/audio/speech"},
    {"name": "audioTranscriptions", "method": "POST", "path": "/v1/audio/transcriptions"},
    {"name": "listModels", "method": "GET", "path": "/v1/models"},
    {"name": "createAssistant", "method": "POST", "path": "/v1/assistants"},
    {"name": "attachAssistantFile", "method": "POST", "path": "/v1/assistants/{assistant_id}/files"},
    {"name": "runAssistant", "method": "POST", "path": "/v1/assistants/{assistant_id}/runs"},
    {"name": "createThread", "method": "POST", "path": "/v1/threads"},
    {"name": "getThreadMessages", "method": "GET", "path": "/v1/threads/{thread_id}/messages"},
    {"name": "addMessageToThread", "method": "POST", "path": "/v1/threads/{thread_id}/messages"},
    {"name": "createRun", "method": "POST", "path": "/v1/threads/{thread_id}/runs"},
    {"name": "getRunSteps", "method": "GET", "path": "/v1/threads/{thread_id}/runs/{run_id}/steps"},
    {"name": "listVectorStores", "method": "GET", "path": "/v1/vector_stores"},
    {"name": "createVectorStore", "method": "POST", "path": "/v1/vector_stores"},
    {"name": "queryVectorStore", "method": "POST", "path": "/v1/vector_stores/{vector_store_id}/queries"},
    {"name": "listVideos", "method": "GET", "path": "/v1/videos"},
    {"name": "createVideo", "method": "POST", "path": "/v1/videos"},
    {"name": "getVideoById", "method": "GET", "path": "/v1/videos/{video_id}"},
    {"name": "getVideoContent", "method": "GET", "path": "/v1/videos/{video_id}/content"},
    {"name": "remixVideo", "method": "POST", "path": "/v1/videos/{video_id}/remix"},
    {"name": "listTools", "method": "GET", "path": "/v1/tools"},
    {"name": "registerTool", "method": "POST", "path": "/v1/tools"},
]

STATUS = {row["name"]: "" for row in CHECKLIST}
RESOURCE_IDS = {}

def write_checklist_to_desktop():
    out_file = os.path.join(DESKTOP, "bifl_checklist.md")
    header = "| Name | Method | Path | Test Status | Actions |\n|------|--------|------|-------------|---------|"
    rows = []
    for row in CHECKLIST:
        status = STATUS.get(row["name"], "")
        rows.append(f"| {row['name']} | {row['method']} | {row['path']} | {status} | Test |")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(header + "\n" + "\n".join(rows))

def set_status(name, passed, why=""):
    # Always mark failed/skipped as ❌ Fail (never blank)
    STATUS[name] = "✅ Passed" if passed else f"❌ Fail {why}".strip()
    write_checklist_to_desktop()

def log_id(label, value):
    RESOURCE_IDS[label] = value
    ids_path = os.path.join(DESKTOP, "bifl_unique_ids.txt")
    with open(ids_path, "a", encoding="utf-8") as f:
        f.write(f"{label}: {value}\n")

def ensure_sample_files():
    # Create test_upload.jsonl if missing
    if not os.path.exists(UPLOAD_JSONL):
        with open(UPLOAD_JSONL, "w", encoding="utf-8") as f:
            f.write('{"text":"Hello, world!"}\n')
    # Create bifl_test_audio.mp3 if missing (dummy silence)
    if not os.path.exists(AUDIO_MP3):
        import wave
        with wave.open(AUDIO_MP3, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b"\0" * 44100 * 2)

ensure_sample_files()

# 1. Upload File (for chaining IDs, agent state)
@pytest.mark.order(1)
def test_uploadFile():
    name = "uploadFile"
    try:
        with open(UPLOAD_JSONL, "rb") as f:
            files = {"file": f}
            data = {"purpose": "fine-tune"}
            r = requests.post(f"{API_BASE}/files", headers=HEADERS, files=files, data=data)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
        file_id = r.json().get("id") or r.json().get("file", {}).get("id")
        log_id("file_id", file_id)
        RESOURCE_IDS["file_id"] = file_id
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(2)
def test_listFiles():
    name = "listFiles"
    try:
        r = requests.get(f"{API_BASE}/files", headers=HEADERS)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
        files = r.json().get("data", [])
        if files:
            RESOURCE_IDS["file_id"] = files[0]["id"]
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(3)
def test_getFile():
    name = "getFile"
    file_id = RESOURCE_IDS.get("file_id")
    if not file_id:
        set_status(name, False, "Missing file_id from previous step")
        pytest.skip("No file_id to fetch")
    try:
        r = requests.get(f"{API_BASE}/files/{file_id}", headers=HEADERS)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(4)
def test_deleteFile():
    name = "deleteFile"
    file_id = RESOURCE_IDS.get("file_id")
    if not file_id:
        set_status(name, False, "Missing file_id from previous step")
        pytest.skip("No file_id to delete")
    try:
        r = requests.delete(f"{API_BASE}/files/{file_id}", headers=HEADERS)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(5)
def test_chatCompletions():
    name = "chatCompletions"
    payload = {
        "model": "gpt-4-1106-preview",
        "messages": [{"role": "user", "content": "Say hello, world!"}]
    }
    try:
        r = requests.post(f"{API_BASE}/chat/completions", headers=HEADERS, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(6)
def test_createEmbedding():
    name = "createEmbedding"
    payload = {"model": "text-embedding-ada-002", "input": "OpenAI"}
    try:
        r = requests.post(f"{API_BASE}/embeddings", headers=HEADERS, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(7)
def test_generateImage():
    name = "generateImage"
    payload = {"prompt": "A cat in space"}
    try:
        r = requests.post(f"{API_BASE}/images/generations", headers=HEADERS, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
        image_id = r.json().get("data", [{}])[0].get("id")
        if image_id:
            RESOURCE_IDS["image_id"] = image_id
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(8)
def test_getImageContent():
    name = "getImageContent"
    image_id = RESOURCE_IDS.get("image_id")
    if not image_id:
        set_status(name, False, "Missing image_id from generateImage")
        pytest.skip("No image_id")
    try:
        r = requests.get(f"{API_BASE}/images/{image_id}/content", headers=HEADERS)
        set_status(name, r.status_code in (200, 404))
        assert r.status_code in (200, 404)
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(9)
def test_audioSpeech():
    name = "audioSpeech"
    payload = {"input": "Test speech", "model": "tts-1", "voice": "alloy"}
    try:
        r = requests.post(f"{API_BASE}/audio/speech", headers=HEADERS, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(10)
def test_audioTranscriptions():
    name = "audioTranscriptions"
    try:
        with open(AUDIO_MP3, "rb") as f:
            files = {"file": f}
            data = {"model": "whisper-1", "language": "en"}
            r = requests.post(f"{API_BASE}/audio/transcriptions", headers=HEADERS, files=files, data=data)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(11)
def test_listModels():
    name = "listModels"
    try:
        r = requests.get(f"{API_BASE}/models", headers=HEADERS)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(12)
def test_createAssistant():
    name = "createAssistant"
    payload = {"name": "TestAssistant", "model": "gpt-4-1106-preview", "tools": [{"type": "retrieval"}]}
    try:
        r = requests.post(f"{API_BASE}/assistants", headers=HEADERS_V2, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
        assistant_id = r.json().get("id")
        if assistant_id:
            RESOURCE_IDS["assistant_id"] = assistant_id
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(13)
def test_attachAssistantFile():
    name = "attachAssistantFile"
    assistant_id = RESOURCE_IDS.get("assistant_id")
    if not assistant_id:
        set_status(name, False, "Missing assistant_id from createAssistant")
        pytest.skip("No assistant_id")
    try:
        with open(UPLOAD_JSONL, "rb") as f:
            files = {"file": f}
            r = requests.post(f"{API_BASE}/assistants/{assistant_id}/files", headers=HEADERS_V2, files=files)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
        file_id = r.json().get("id")
        if file_id:
            log_id("assistant_file_id", file_id)
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(14)
def test_runAssistant():
    name = "runAssistant"
    assistant_id = RESOURCE_IDS.get("assistant_id")
    if not assistant_id:
        set_status(name, False, "Missing assistant_id from createAssistant")
        pytest.skip("No assistant_id")
    payload = {"instructions": "Just say 'pong'."}
    try:
        r = requests.post(f"{API_BASE}/assistants/{assistant_id}/runs", headers=HEADERS_V2, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
        run_id = r.json().get("run_id")
        if run_id:
            RESOURCE_IDS["assistant_run_id"] = run_id
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(15)
def test_createThread():
    name = "createThread"
    payload = {"messages": [{"role": "user", "content": "Start thread"}]}
    try:
        r = requests.post(f"{API_BASE}/threads", headers=HEADERS_V2, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
        thread_id = r.json().get("id")
        if thread_id:
            RESOURCE_IDS["thread_id"] = thread_id
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(16)
def test_getThreadMessages():
    name = "getThreadMessages"
    thread_id = RESOURCE_IDS.get("thread_id")
    if not thread_id:
        set_status(name, False, "Missing thread_id from createThread")
        pytest.skip("No thread_id")
    try:
        r = requests.get(f"{API_BASE}/threads/{thread_id}/messages", headers=HEADERS_V2)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(17)
def test_addMessageToThread():
    name = "addMessageToThread"
    thread_id = RESOURCE_IDS.get("thread_id")
    if not thread_id:
        set_status(name, False, "Missing thread_id from createThread")
        pytest.skip("No thread_id")
    payload = {"role": "user", "content": "Another message"}
    try:
        r = requests.post(f"{API_BASE}/threads/{thread_id}/messages", headers=HEADERS_V2, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(18)
def test_createRun():
    name = "createRun"
    thread_id = RESOURCE_IDS.get("thread_id")
    assistant_id = RESOURCE_IDS.get("assistant_id")
    if not thread_id or not assistant_id:
        set_status(name, False, "Missing thread_id or assistant_id")
        pytest.skip("Need thread_id and assistant_id")
    payload = {"assistant_id": assistant_id, "instructions": "Reply with 'run OK'."}
    try:
        r = requests.post(f"{API_BASE}/threads/{thread_id}/runs", headers=HEADERS_V2, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
        run_id = r.json().get("run_id")
        if run_id:
            RESOURCE_IDS["thread_run_id"] = run_id
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(19)
def test_getRunSteps():
    name = "getRunSteps"
    thread_id = RESOURCE_IDS.get("thread_id")
    run_id = RESOURCE_IDS.get("thread_run_id")
    if not thread_id or not run_id:
        set_status(name, False, "Missing thread_id or thread_run_id")
        pytest.skip("Need thread_id and run_id")
    try:
        r = requests.get(f"{API_BASE}/threads/{thread_id}/runs/{run_id}/steps", headers=HEADERS_V2)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(20)
def test_listVectorStores():
    name = "listVectorStores"
    try:
        r = requests.get(f"{API_BASE}/vector_stores", headers=HEADERS_V2)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(21)
def test_createVectorStore():
    name = "createVectorStore"
    payload = {"name": "TestStore"}
    try:
        r = requests.post(f"{API_BASE}/vector_stores", headers=HEADERS_V2, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
        store_id = r.json().get("id")
        if store_id:
            RESOURCE_IDS["vector_store_id"] = store_id
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(22)
def test_queryVectorStore():
    name = "queryVectorStore"
    store_id = RESOURCE_IDS.get("vector_store_id")
    if not store_id:
        set_status(name, False, "Missing vector_store_id from createVectorStore")
        pytest.skip("No vector_store_id")
    payload = {"query": "test"}
    try:
        r = requests.post(f"{API_BASE}/vector_stores/{store_id}/queries", headers=HEADERS_V2, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(23)
def test_listVideos():
    name = "listVideos"
    try:
        r = requests.get(f"{API_BASE}/videos", headers=HEADERS)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
        videos = r.json().get("data", [])
        if videos:
            RESOURCE_IDS["video_id"] = videos[0].get("id")
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(24)
def test_createVideo_and_chain_download_and_remix():
    # Chain for both sora-2 and sora-2-pro
    for model, prompt, suffix in [
        ("sora-2", "aurora", "sora2"),
        ("sora-2-pro", "car", "sora2pro")
    ]:
        name_create = f"createVideo_{suffix}"
        name_download = f"getVideoContent_{suffix}"
        name_remix = f"remixVideo_{suffix}"
        name_remix_download = f"getVideoContent_{suffix}_remix"

        # 1. Create
        r = requests.post(f"{API_BASE}/videos", headers=HEADERS, json={
            "prompt": prompt,
            "seconds": "4",
            "model": model
        })
        set_status("createVideo", r.status_code == 200)
        assert r.status_code == 200
        video_id = r.json().get("id") or r.json().get("video", {}).get("id")
        log_id(f"video_id_{suffix}", video_id)

        # 2. Poll for done
        def poll_until_done(vid, timeout=180):
            t0 = time.time()
            while time.time() - t0 < timeout:
                resp = requests.get(f"{API_BASE}/videos/{vid}", headers=HEADERS)
                if resp.status_code == 200 and resp.json().get("status") == "completed":
                    return True
                time.sleep(5)
            return False

        if not poll_until_done(video_id):
            set_status("getVideoContent", False, f"{model} video did not finish in time")
            continue

        # 3. Download
        resp = requests.get(f"{API_BASE}/videos/{video_id}/content", headers=HEADERS)
        set_status("getVideoContent", resp.status_code == 200)
        assert resp.status_code == 200
        path = os.path.join(DOWNLOADS, f"{suffix}_{video_id}.mp4")
        with open(path, "wb") as f:
            f.write(resp.content)
        log_id(f"video_file_{suffix}", path)

        # Save for getVideoById
        RESOURCE_IDS[f"video_id_{suffix}"] = video_id

        # 4. Remix
        remix = requests.post(f"{API_BASE}/videos/{video_id}/remix", headers=HEADERS, json={"prompt": f"Make it blue and red"})
        set_status("remixVideo", remix.status_code == 200)
        assert remix.status_code == 200
        remix_id = remix.json().get("id") or remix.json().get("video", {}).get("id")
        log_id(f"remix_id_{suffix}", remix_id)
        if not poll_until_done(remix_id):
            set_status("getVideoContent", False, f"{model} remix did not finish in time")
            continue

        # 5. Download remix
        remix_resp = requests.get(f"{API_BASE}/videos/{remix_id}/content", headers=HEADERS)
        set_status("getVideoContent", remix_resp.status_code == 200)
        assert remix_resp.status_code == 200
        remix_path = os.path.join(DOWNLOADS, f"{suffix}_remix_{remix_id}.mp4")
        with open(remix_path, "wb") as f:
            f.write(remix_resp.content)
        log_id(f"remix_file_{suffix}", remix_path)

        # Set global for later tests
        RESOURCE_IDS[f"remix_id_{suffix}"] = remix_id

@pytest.mark.order(25)
def test_getVideoById():
    name = "getVideoById"
    video_id = RESOURCE_IDS.get("video_id_sora2") or RESOURCE_IDS.get("video_id")
    if not video_id:
        set_status(name, False, "Missing video_id from createVideo")
        pytest.skip("No video_id")
    try:
        r = requests.get(f"{API_BASE}/videos/{video_id}", headers=HEADERS)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(26)
def test_getVideoContent():
    name = "getVideoContent"
    video_id = RESOURCE_IDS.get("video_id_sora2") or RESOURCE_IDS.get("video_id")
    if not video_id:
        set_status(name, False, "Missing video_id from createVideo")
        pytest.skip("No video_id")
    try:
        resp = requests.get(f"{API_BASE}/videos/{video_id}/content", headers=HEADERS)
        set_status(name, resp.status_code == 200)
        assert resp.status_code == 200
        path = os.path.join(DOWNLOADS, f"video_{video_id}_content.mp4")
        with open(path, "wb") as f:
            f.write(resp.content)
        log_id(f"video_file_content", path)
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(27)
def test_remixVideo():
    name = "remixVideo"
    video_id = RESOURCE_IDS.get("video_id_sora2") or RESOURCE_IDS.get("video_id")
    if not video_id:
        set_status(name, False, "Missing video_id from createVideo")
        pytest.skip("No video_id")
    try:
        remix = requests.post(f"{API_BASE}/videos/{video_id}/remix", headers=HEADERS, json={"prompt": "Colorize"})
        set_status(name, remix.status_code == 200)
        assert remix.status_code == 200
        remix_id = remix.json().get("id") or remix.json().get("video", {}).get("id")
        log_id("remix_id", remix_id)
        RESOURCE_IDS["remix_id"] = remix_id
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(28)
def test_listTools():
    name = "listTools"
    try:
        r = requests.get(f"{API_BASE}/tools", headers=HEADERS_V2)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e

@pytest.mark.order(29)
def test_registerTool():
    name = "registerTool"
    payload = {"type": "retrieval"}
    try:
        r = requests.post(f"{API_BASE}/tools", headers=HEADERS_V2, json=payload)
        set_status(name, r.status_code == 200)
        assert r.status_code == 200
    except Exception as e:
        set_status(name, False, str(e))
        raise e



def pytest_sessionfinish(session, exitstatus):
    write_checklist_to_desktop()
    ids_path = os.path.join(DESKTOP, "bifl_unique_ids.txt")
    print(f"All IDs logged at: {ids_path}")

