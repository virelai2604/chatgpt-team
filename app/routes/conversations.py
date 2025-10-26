# app/routes/conversations.py
# BIFL v2.2 — Unified Conversations API
# Handles local conversation persistence + optional relay sync.

import os
import sqlite3
import time
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from app.api.forward import forward_openai


router = APIRouter(prefix="/v1/conversations", tags=["Conversations"])

# === Config ===
CONV_DIR = os.getenv("CONVERSATIONS_DIR", "data/conversations")
DB_PATH = os.path.join(CONV_DIR, "conversations.db")
os.makedirs(CONV_DIR, exist_ok=True)

# === Init local DB ===
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            system TEXT,
            created_at INTEGER
        );
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conv_id TEXT,
            role TEXT,
            content TEXT,
            created_at INTEGER
        );
        """)
init_db()

# === Helpers ===
def get_conn():
    return sqlite3.connect(DB_PATH)

def conv_exists(conv_id: str) -> bool:
    with get_conn() as db:
        row = db.execute("SELECT id FROM conversations WHERE id = ?", (conv_id,)).fetchone()
        return bool(row)

def list_conversations() -> List[Dict[str, Any]]:
    with get_conn() as db:
        rows = db.execute("SELECT id, title, created_at FROM conversations ORDER BY created_at DESC").fetchall()
        return [{"id": r[0], "title": r[1], "created_at": r[2]} for r in rows]

def list_messages(conv_id: str) -> List[Dict[str, Any]]:
    with get_conn() as db:
        rows = db.execute(
            "SELECT role, content, created_at FROM messages WHERE conv_id = ? ORDER BY id ASC",
            (conv_id,)
        ).fetchall()
        return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in rows]

# === Routes ===

@router.get("/")
async def get_conversation_list():
    """List all stored conversations."""
    return JSONResponse(content={"object": "list", "data": list_conversations()})


@router.post("/")
async def create_conversation(body: Dict[str, Any] = Body(...)):
    """Create a new conversation."""
    title = body.get("title", "Untitled")
    conv_id = body.get("id") or f"conv_{int(time.time()*1000)}"
    system = body.get("system", "You are a helpful assistant.")
    created_at = int(time.time())

    with get_conn() as db:
        db.execute(
            "INSERT INTO conversations (id, title, system, created_at) VALUES (?, ?, ?, ?)",
            (conv_id, title, system, created_at),
        )
        db.commit()

    return JSONResponse(
        content={"object": "conversation", "id": conv_id, "title": title, "system": system, "created_at": created_at}
    )


@router.get("/{conv_id}")
async def get_conversation(conv_id: str):
    """Retrieve a conversation and all its messages."""
    if not conv_exists(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = list_messages(conv_id)
    return JSONResponse(content={"object": "conversation", "id": conv_id, "messages": messages})


@router.post("/{conv_id}/messages")
async def add_message(conv_id: str, body: Dict[str, Any] = Body(...)):
    """Add a message to a conversation."""
    if not conv_exists(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    role = body.get("role", "user")
    content = body.get("content", "")
    created_at = int(time.time())

    with get_conn() as db:
        db.execute(
            "INSERT INTO messages (conv_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conv_id, role, content, created_at),
        )
        db.commit()

    return JSONResponse(
        content={"object": "message", "conv_id": conv_id, "role": role, "content": content, "created_at": created_at}
    )


@router.get("/{conv_id}/summary")
async def summarize_conversation(conv_id: str, model: str = "gpt-5-codex"):
    """Summarize a conversation using the relay /v1/responses."""
    if not conv_exists(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = list_messages(conv_id)
    text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])

    # Forward to relay for summarization
    try:
        resp = await forward_openai(
            path="/v1/responses",
            method="POST",
            json={
                "model": model,
                "input": f"Summarize this conversation:\n{text}",
                "temperature": 0.4,
                "stream": False,
            },
        )
        return JSONResponse(content={"object": "summary", "conversation_id": conv_id, "summary": resp})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str):
    """Delete a conversation and its messages."""
    if not conv_exists(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    with get_conn() as db:
        db.execute("DELETE FROM messages WHERE conv_id = ?", (conv_id,))
        db.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        db.commit()

    return JSONResponse(content={"deleted": conv_id})


# === Tool for /v1/responses integration ===
async def execute_conversation_tool(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool entrypoint to retrieve or summarize conversations via tools[].
    Example:
      { "type": "conversation_summary", "parameters": {"conv_id": "conv_123"} }
    """
    try:
        t_type = tool.get("type")
        params = tool.get("parameters", {})

        if t_type == "conversation_summary":
            conv_id = params.get("conv_id")
            if not conv_id:
                raise ValueError("Missing conv_id for conversation_summary")
            messages = list_messages(conv_id)
            text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            resp = await forward_openai(
                path="/v1/responses",
                method="POST",
                json={"model": "gpt-5-codex", "input": f"Summarize:\n{text}", "stream": False},
            )
            return {"type": "conversation_summary", "summary": resp}

        return {"error": f"Unsupported tool type: {t_type}"}
    except Exception as e:
        return {"error": str(e)}
