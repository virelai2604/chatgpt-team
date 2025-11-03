"""
conversations.py — OpenAI-Compatible /v1/conversations Endpoint
───────────────────────────────────────────────────────────────
Implements conversation persistence compatible with:
  • openai-python SDK v2.61
  • openai-node SDK v6.7.0
  • OpenAI API Reference (2025-10)

Supports:
  • GET /v1/conversations            → list all conversations
  • GET /v1/conversations/{id}       → retrieve a specific conversation
  • POST /v1/conversations           → create new conversation (store or proxy)
  • POST /v1/conversations/{id}/messages → append a new message
Provides hybrid persistence (online-first + local SQLite cache).
"""

import os
import json
import sqlite3
import httpx
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_AGENT = "openai-python/2.61.0"
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))
DB_PATH = os.getenv("CONVERSATION_DB_PATH", "data/conversations.db")

# ------------------------------------------------------------
# Local persistence helpers
# ------------------------------------------------------------
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            created TIMESTAMP,
            last_updated TIMESTAMP,
            data TEXT
        )
    """)
    conn.close()

def save_conversation(conv_id: str, data: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO conversations (id, title, created, last_updated, data) VALUES (?, ?, ?, ?, ?)",
        (
            conv_id,
            data.get("title", "Untitled"),
            data.get("created", datetime.utcnow().isoformat()),
            datetime.utcnow().isoformat(),
            json.dumps(data),
        ),
    )
    conn.commit()
    conn.close()

def get_conversation(conv_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT data FROM conversations WHERE id = ?", (conv_id,))
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

def list_conversations_local():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT id, title, created, last_updated FROM conversations ORDER BY last_updated DESC")
    results = [
        {"id": r[0], "title": r[1], "created": r[2], "last_updated": r[3]}
        for r in cur.fetchall()
    ]
    conn.close()
    return results

init_db()

# ------------------------------------------------------------
# Network helper
# ------------------------------------------------------------
def build_headers():
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }


# ------------------------------------------------------------
# GET /v1/conversations → list conversations
# ------------------------------------------------------------
@router.get("")
async def list_conversations():
    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.get(f"{OPENAI_API_BASE}/conversations", headers=headers)
            if resp.status_code == 200:
                return JSONResponse(resp.json(), status_code=200)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online list failed: {e}, using local cache.")
    return JSONResponse({"object": "list", "data": list_conversations_local()}, status_code=200)


# ------------------------------------------------------------
# GET /v1/conversations/{id} → retrieve conversation
# ------------------------------------------------------------
@router.get("/{conv_id}")
async def retrieve_conversation(conv_id: str):
    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.get(f"{OPENAI_API_BASE}/conversations/{conv_id}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                save_conversation(conv_id, data)
                return JSONResponse(data, status_code=200)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online retrieve failed: {e}, falling back.")
    local = get_conversation(conv_id)
    if local:
        return JSONResponse(local, status_code=200)
    return JSONResponse({"error": "Conversation not found"}, status_code=404)


# ------------------------------------------------------------
# POST /v1/conversations → create conversation
# ------------------------------------------------------------
@router.post("")
async def create_conversation(request: Request):
    """Creates a new conversation (upstream or local)."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.post(f"{OPENAI_API_BASE}/conversations", headers=headers, json=body)
            if resp.status_code in (200, 201):
                data = resp.json()
                save_conversation(data.get("id", f"local-{datetime.utcnow().timestamp()}"), data)
                return JSONResponse(data, status_code=resp.status_code)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online create failed: {e}, saving locally.")
    # fallback local save
    conv_id = f"local-{datetime.utcnow().timestamp()}"
    data = {"id": conv_id, "title": body.get("title", "Untitled"), "messages": [], "created": datetime.utcnow().isoformat()}
    save_conversation(conv_id, data)
    return JSONResponse(data, status_code=201)


# ------------------------------------------------------------
# POST /v1/conversations/{id}/messages → append message
# ------------------------------------------------------------
@router.post("/{conv_id}/messages")
async def append_message(conv_id: str, request: Request):
    """Appends a message to a conversation (local + upstream)."""
    try:
        msg = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.post(f"{OPENAI_API_BASE}/conversations/{conv_id}/messages", headers=headers, json=msg)
            if resp.status_code in (200, 201):
                return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online append failed: {e}, using local.")

    local = get_conversation(conv_id)
    if local:
        local.setdefault("messages", []).append(
            {"role": msg.get("role", "user"), "content": msg.get("content", ""), "timestamp": datetime.utcnow().isoformat()}
        )
        save_conversation(conv_id, local)
        return JSONResponse(local, status_code=200)

    return JSONResponse({"error": "Conversation not found"}, status_code=404)
