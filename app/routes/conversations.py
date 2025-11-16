"""
conversations.py — /v1/conversations (plus local cache)
────────────────────────────────────────────────────────
Implements OpenAI Conversations endpoints with an optional local
SQLite/JSON cache for resilience and offline listing.
"""

import os
import json
import sqlite3
from datetime import datetime

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.utils.logger import relay_log as log

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RELAY_TIMEOUT = int(os.getenv("RELAY_TIMEOUT", "60"))

DB_PATH = os.getenv("CONVERSATIONS_DB", "data/conversations.db")
USER_AGENT = os.getenv("RELAY_USER_AGENT", "chatgpt-team-relay/1.0")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_conversation(conv_id: str, data: dict):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            INSERT INTO conversations (id, data, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                data=excluded.data,
                updated_at=excluded.updated_at
            """,
            (conv_id, json.dumps(data), datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_conversation(conv_id: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "SELECT data FROM conversations WHERE id = ?",
            (conv_id,),
        )
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return None
    finally:
        conn.close()


def list_conversations_local(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "SELECT data FROM conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        )
        return [json.loads(r[0]) for r in cur.fetchall()]
    finally:
        conn.close()


init_db()


def build_headers():
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }


@router.get("")
async def list_conversations():
    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.get(
                f"{OPENAI_API_BASE.rstrip('/')}/conversations", headers=headers
            )
            if resp.status_code == 200:
                return JSONResponse(resp.json(), status_code=200)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online list failed: {e}, using local cache.")
    return JSONResponse(
        {"object": "list", "data": list_conversations_local()}, status_code=200
    )


@router.get("/{conv_id}")
async def retrieve_conversation(conv_id: str):
    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.get(
                f"{OPENAI_API_BASE.rstrip('/')}/conversations/{conv_id}",
                headers=headers,
            )
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


@router.post("")
async def create_conversation(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{OPENAI_API_BASE.rstrip('/')}/conversations",
                headers=headers,
                json=body,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                save_conversation(
                    data.get("id", f"local-{datetime.utcnow().timestamp()}"), data
                )
                return JSONResponse(data, status_code=resp.status_code)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online create failed: {e}, saving locally.")
    conv_id = f"local-{datetime.utcnow().timestamp()}"
    data = {
        "id": conv_id,
        "title": body.get("title", "Untitled"),
        "messages": [],
        "created": datetime.utcnow().isoformat(),
    }
    save_conversation(conv_id, data)
    return JSONResponse(data, status_code=201)


@router.post("/{conv_id}/messages")
async def append_message(conv_id: str, request: Request):
    try:
        msg = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{OPENAI_API_BASE.rstrip('/')}/conversations/{conv_id}/messages",
                headers=headers,
                json=msg,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                existing = get_conversation(conv_id) or {"id": conv_id, "messages": []}
                messages = existing.get("messages", [])
                messages.append(msg)
                existing["messages"] = messages
                save_conversation(conv_id, existing)
                return JSONResponse(data, status_code=resp.status_code)
        except httpx.RequestError as e:
            log.warning(f"[Conversations] Online append failed: {e}, local only.")

    existing = get_conversation(conv_id) or {"id": conv_id, "messages": []}
    messages = existing.get("messages", [])
    messages.append(msg)
    existing["messages"] = messages
    save_conversation(conv_id, existing)
    return JSONResponse(existing, status_code=200)
