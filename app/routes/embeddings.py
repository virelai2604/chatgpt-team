# app/routes/embeddings.py
# BIFL v2.2 — Unified Embeddings API
# Compatible with OpenAI SDK 2.6.1 / GPT-5-Codex relay.
# Supports local persistence + relay passthrough.

import os
import sqlite3
import time
from typing import Any, Dict, List, Union
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
from app.api.forward import forward_openai


router = APIRouter(prefix="/v1/embeddings", tags=["Embeddings"])

# === Config ===
EMBED_DIR = os.getenv("EMBEDDINGS_DIR", "data/embeddings")
DB_PATH = os.path.join(EMBED_DIR, "embeddings.db")
os.makedirs(EMBED_DIR, exist_ok=True)

# === Init DB ===
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            id TEXT PRIMARY KEY,
            model TEXT,
            input TEXT,
            dims INTEGER,
            created_at INTEGER
        );
        """)
init_db()

def save_metadata(model: str, text: str, dims: int):
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO embeddings (id, model, input, dims, created_at) VALUES (?, ?, ?, ?, ?)",
            (f"emb_{int(time.time()*1000)}", model, text[:200], dims, int(time.time())),
        )
        db.commit()


# === /v1/embeddings ===
@router.post("/")
async def create_embedding(
    body: Dict[str, Any] = Body(
        ...,
        example={
            "model": "text-embedding-3-large",
            "input": ["Sample text A", "Sample text B"]
        }
    )
):
    """
    Create text or multimodal embeddings.
    - Default model: text-embedding-3-large
    - Logs metadata locally
    """
    model = body.get("model", "text-embedding-3-large")
    input_data: Union[str, List[str]] = body.get("input")

    if not input_data:
        raise HTTPException(status_code=400, detail="Missing input for embeddings")

    try:
        resp = await forward_openai(
            path="/v1/embeddings",
            method="POST",
            json={"model": model, "input": input_data},
        )
        if not resp or "data" not in resp:
            raise HTTPException(status_code=502, detail="No embedding data returned")

        # Save one record per input item
        for item in resp["data"]:
            dims = len(item.get("embedding", []))
            text = item.get("input", str(input_data))
            save_metadata(model, text, dims)

        return JSONResponse(status_code=200, content=resp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")


# === /v1/embeddings/history ===
@router.get("/history")
async def list_embeddings():
    """List locally cached embedding metadata."""
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            "SELECT id, model, input, dims, created_at FROM embeddings ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
        data = [
            {"id": r[0], "model": r[1], "input": r[2], "dims": r[3], "created_at": r[4]}
            for r in rows
        ]
    return JSONResponse(content={"object": "list", "data": data})


# === /v1/embeddings/search (optional local cosine match) ===
@router.post("/search")
async def search_embeddings(body: Dict[str, Any] = Body(...)):
    """
    Local search placeholder (to be integrated with vector_stores.py).
    Accepts { "query": "...", "limit": 10 }
    """
    query = body.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Missing query")
    limit = body.get("limit", 10)
    # In BIFL v2.2 this endpoint simply proxies for now
    try:
        resp = await forward_openai(
            path="/v1/embeddings",
            method="POST",
            json={"model": "text-embedding-3-large", "input": query},
        )
        dims = len(resp["data"][0]["embedding"])
        save_metadata("text-embedding-3-large", query, dims)
        return JSONResponse(content={"object": "embedding_search", "query": query, "dims": dims, "limit": limit})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search embedding failed: {e}")


# === Tool interface for /v1/responses ===
async def execute_embedding_tool(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool entrypoint for embedding generation within /v1/responses.
    Example:
      { "type": "embedding_create", "parameters": {"input": "text to embed"} }
    """
    try:
        params = tool.get("parameters", {})
        text = params.get("input")
        model = params.get("model", "text-embedding-3-large")
        resp = await forward_openai(
            path="/v1/embeddings", method="POST", json={"model": model, "input": text}
        )
        dims = len(resp["data"][0]["embedding"])
        save_metadata(model, text, dims)
        return {"type": "embedding_create", "dims": dims, "model": model}
    except Exception as e:
        return {"error": str(e)}
