# app/routes/vector_stores.py
# BIFL v2.2 — Unified Vector Store API
# Manages both local and relay-based embeddings and vector batches.
# Compatible with OpenAI SDK 2.6.1 and /v1/vector_stores architecture.

import os
import json
import time
import uuid
import math
import sqlite3
import numpy as np
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from app.api.forward import forward_openai


router = APIRouter(prefix="/v1/vector_stores", tags=["Vector Stores"])

# === Config ===
VECTOR_DIR = os.getenv("VECTOR_DIR", "data/vector_stores")
DB_PATH = os.path.join(VECTOR_DIR, "vectors.db")
os.makedirs(VECTOR_DIR, exist_ok=True)

# === Init DB ===
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS vector_stores (
            id TEXT PRIMARY KEY,
            name TEXT,
            created_at INTEGER,
            status TEXT,
            metadata TEXT
        );
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS vectors (
            id TEXT PRIMARY KEY,
            store_id TEXT,
            embedding TEXT,
            content TEXT,
            created_at INTEGER
        );
        """)
init_db()


# === Helper Functions ===

def save_vector(store_id: str, embedding: List[float], content: str):
    """Save a single vector locally."""
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO vectors (id, store_id, embedding, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), store_id, json.dumps(embedding), content, int(time.time())),
        )
        db.commit()


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


# === ROUTES ===

@router.get("/")
async def list_vector_stores():
    """List all local and relay vector stores."""
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute("SELECT id, name, created_at, status FROM vector_stores ORDER BY created_at DESC").fetchall()
        local_data = [
            {"id": r[0], "object": "vector_store", "name": r[1], "created_at": r[2], "status": r[3]}
            for r in rows
        ]

    try:
        relay = await forward_openai(path="/v1/vector_stores", method="GET")
        if relay and "data" in relay:
            return JSONResponse(content={"object": "list", "local": local_data, "relay": relay["data"]})
    except Exception:
        pass
    return JSONResponse(content={"object": "list", "local": local_data, "relay": []})


@router.post("/")
async def create_vector_store(body: Dict[str, Any] = Body(...)):
    """Create a new vector store locally and on the relay."""
    name = body.get("name", f"store_{int(time.time())}")
    metadata = body.get("metadata", {})
    store_id = str(uuid.uuid4())
    created_at = int(time.time())

    # Save locally
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO vector_stores (id, name, created_at, status, metadata) VALUES (?, ?, ?, ?, ?)",
            (store_id, name, created_at, "ready", json.dumps(metadata)),
        )
        db.commit()

    # Try to create relay store
    try:
        relay = await forward_openai(
            path="/v1/vector_stores",
            method="POST",
            json={"id": store_id, "name": name, "metadata": metadata},
        )
    except Exception as e:
        relay = {"error": f"Relay creation failed: {e}"}

    return JSONResponse(content={
        "object": "vector_store",
        "id": store_id,
        "name": name,
        "created_at": created_at,
        "relay": relay,
    })


@router.post("/{store_id}/batches")
async def create_vector_batch(store_id: str, body: Dict[str, Any] = Body(...)):
    """Batch import embeddings into a store."""
    file_ids = body.get("file_ids", [])
    vectors = body.get("vectors", [])
    if not vectors and not file_ids:
        raise HTTPException(status_code=400, detail="No vectors or file_ids provided")

    # Save locally
    for v in vectors:
        emb = v.get("embedding")
        text = v.get("content", "")
        if emb:
            save_vector(store_id, emb, text)

    # Send to relay
    try:
        relay = await forward_openai(
            path=f"/v1/vector_stores/{store_id}/batches",
            method="POST",
            json={"file_ids": file_ids},
        )
    except Exception as e:
        relay = {"error": f"Relay batch upload failed: {e}"}

    return JSONResponse(content={
        "object": "batch_import",
        "store_id": store_id,
        "count": len(vectors),
        "relay": relay,
    })


@router.post("/{store_id}/query")
async def query_vector_store(store_id: str, body: Dict[str, Any] = Body(...)):
    """
    Perform semantic search within a local vector store.
    Uses cosine similarity between input query and stored vectors.
    """
    query_vec = body.get("embedding")
    limit = int(body.get("limit", 5))
    if not query_vec:
        raise HTTPException(status_code=400, detail="Missing query embedding")

    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            "SELECT embedding, content FROM vectors WHERE store_id = ?", (store_id,)
        ).fetchall()

    scored = []
    for emb_json, content in rows:
        emb = json.loads(emb_json)
        score = cosine_similarity(query_vec, emb)
        scored.append({"content": content, "score": round(score, 4)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return JSONResponse(content={
        "object": "vector_query",
        "store_id": store_id,
        "results": scored[:limit],
        "total": len(scored),
    })


@router.get("/{store_id}")
async def get_vector_store(store_id: str):
    """Retrieve a specific vector store by ID."""
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute("SELECT id, name, status, created_at, metadata FROM vector_stores WHERE id = ?", (store_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vector store not found")
    return JSONResponse(content={
        "id": row[0], "name": row[1], "status": row[2], "created_at": row[3], "metadata": json.loads(row[4])
    })


@router.get("/{store_id}/batches")
async def list_batches(store_id: str):
    """List all batches associated with a store."""
    try:
        relay = await forward_openai(path=f"/v1/vector_stores/{store_id}/batches", method="GET")
        return JSONResponse(content={"object": "vector_batches", "relay": relay})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Relay batch listing failed: {e}")
