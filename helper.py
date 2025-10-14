import os
from datetime import datetime

# ---- CONFIG ----
BASE_URL = "https://chatgpt-team-relay.onrender.com/v1"
DOWNLOADS_DIR = r"C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\Downloads"
DESKTOP = os.path.expandvars(r"%USERPROFILE%\Desktop")  # Or set your username if needed
RESULTS_MD = os.path.join(DESKTOP, "openai_relay_test_results.md")
IDS_TXT = os.path.join(DESKTOP, "openai_relay_test_ids.txt")
SAMPLES_DIR = r"C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\samples files"
JSONL_FILE = os.path.join(SAMPLES_DIR, "test_upload.jsonl")
AUDIO_FILE = os.path.join(SAMPLES_DIR, "bifl_test_audio.mp3")
HEADERS_V2 = {"OpenAI-Beta": "assistants=v2"}

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def log_result(test, endpoint, status, extra=""):
    with open(RESULTS_MD, "a", encoding="utf-8") as f:
        f.write(f"- {datetime.now().isoformat()} | **{test}** | `{endpoint}` | {status} | {extra}\n")

def log_id(endpoint, unique_id):
    with open(IDS_TXT, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {endpoint} | {unique_id}\n")
