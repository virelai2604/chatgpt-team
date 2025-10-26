# app/routes/models.py
# BIFL v2.2 — Unified Model Registry API
# Lists, caches, and manages both local and relay models.
# Supports hybrid mode (local cache + live OpenAI relay sync).

import os
import json
import sqlite3
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from app.api.forward import forward_openai


router = APIRouter(prefix="/v1/models", tags=["Models"])

# === Config ===
MODELS_DB = os.getenv("MODELS_DB", "data/models/models.db")
os.makedirs(os.path.dirname(MODELS_DB), exist_ok=True)

# === Init Local DB ===
def init_db():
    with sqlite3.connect(MODELS_DB) as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id TEXT PRIMARY KEY,
            object TEXT,
            note TEXT,
            source TEXT,
            updated_at INTEGER
        );
        """)
init_db()

# === Helpers ===
def cache_models(models: List[Dict[str, Any]], source: str = "relay"):
    with sqlite3.connect(MODELS_DB) as db:
        for m in models:
            db.execute(
                "INSERT OR REPLACE INTO models (id, object, note, source, updated_at) VALUES (?, ?, ?, ?, ?)",
                (m.get("id"), m.get("object", "model"), m.get("note", ""), source, int(time.time())),
            )
        db.commit()

def list_local_models() -> List[Dict[str, Any]]:
    with sqlite3.connect(MODELS_DB) as db:
        rows = db.execute("SELECT id, object, note, source, updated_at FROM models ORDER BY updated_at DESC").fetchall()
        return [
            {"id": r[0], "object": r[1], "note": r[2], "source": r[3], "updated_at": r[4]}
            for r in rows
        ]

# === Preload Common GPT-5/O-Series Models ===
DEFAULT_MODELS = [
    {"id": "gpt-5", "object": "model", "note": "GPT-5 general reasoning engine"},
    {"id": "gpt-5-codex", "object": "model", "note": "Code-optimized GPT-5 variant"},
    {"id": "gpt-5-pro", "object": "model", "note": "High-reasoning GPT-5 Pro"},
    {"id": "sora-2-pro", "object": "model", "note": "Video generation model"},
    {"id": "text-embedding-3-large", "object": "model", "note": "Latest text embedding model"},
    {"id": "o3-pro", "object": "model", "note": "Operator optimization model"},
]
cache_models(DEFAULT_MODELS, source="local")


# === Routes ===

@router.get("/")
async def list_models():
    """
    List available models.
    - Combines cached local entries and live relay models.
    - Fallbacks to local cache if relay unavailable.
    """
    try:
        relay = await forward_openai(path="/v1/models", method="GET")
        if relay and "data" in relay:
            cache_models(relay["data"], source="relay")
            models = list_local_models()
            return JSONResponse(content={"object": "list", "data": models})
        else:
            raise Exception("Relay returned no data")
    except Exception as e:
        print(f"[WARN] Relay sync failed: {e}")
        return JSONResponse(content={"object": "list", "data": list_local_models(), "cached": True})


@router.get("/{model_id}")
async def get_model(model_id: str):
    """
    Retrieve a specific model by ID.
    Tries local cache first, then queries the relay.
    """
    with sqlite3.connect(MODELS_DB) as db:
        row = db.execute("SELECT id, note, source, updated_at FROM models WHERE id = ?", (model_id,)).fetchone()

    if row:
        model_info = {"id": row[0], "object": "model", "note": row[1], "source": row[2], "updated_at": row[3]}
    else:
        model_info = None

    try:
        relay = await forward_openai(path=f"/v1/models/{model_id}", method="GET")
        if relay:
            cache_models([relay], source="relay")
            model_info = relay
    except Exception:
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found locally or via relay")

    return JSONResponse(content=model_info or {"error": "Model not found"})


@router.post("/refresh")
async def refresh_models():
    """Manually force-refresh model list from relay."""
    try:
        relay = await forward_openai(path="/v1/models", method="GET")
        if not relay or "data" not in relay:
            raise HTTPException(status_code=502, detail="Relay did not return model data")
        cache_models(relay["data"], source="relay")
        return JSONResponse(content={"refreshed": True, "count": len(relay["data"])})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model refresh failed: {e}")


# === Internal Tools for /v1/responses Integration ===
async def execute_model_tool(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool entrypoint for /v1/responses, enabling dynamic model queries.
    Example:
      { "type": "model_lookup", "parameters": {"id": "gpt-5-pro"} }
    """
    try:
        params = tool.get("parameters", {})
        model_id = params.get("id")
        if not model_id:
            return {"error": "Missing model_id parameter"}
        model = await get_model(model_id)
        return {"type": "model_lookup", "model": model.body}
    except Exception as e:
        return {"error": str(e)}
