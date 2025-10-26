# app/routes/images.py
# BIFL v2.2 — Unified Hybrid Image API
# Compatible with OpenAI SDK 2.6.1 and GPT-5 unified responses tools.
# Supports image generation, editing, and content proxying.

import os
import io
import time
import uuid
import aiofiles
import sqlite3
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, Dict, Any
from app.api.forward import forward_openai


router = APIRouter(prefix="/v1/images", tags=["Images"])

# === Config ===
IMAGES_DIR = os.getenv("IMAGES_DIR", "data/images")
DB_PATH = os.path.join(IMAGES_DIR, "images.db")
os.makedirs(IMAGES_DIR, exist_ok=True)

# === Init DB ===
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            prompt TEXT,
            model TEXT,
            file_path TEXT,
            url TEXT,
            created_at INTEGER
        );
        """)
init_db()


# === Helpers ===
def save_metadata(prompt: str, model: str, file_path: str, url: Optional[str]):
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO images (id, prompt, model, file_path, url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), prompt, model, file_path, url, int(time.time())),
        )
        db.commit()


def list_images(limit: int = 20):
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute("SELECT id, prompt, model, url, created_at FROM images ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [
            {"id": r[0], "object": "image", "prompt": r[1], "model": r[2], "url": r[3], "created_at": r[4]}
            for r in rows
        ]


# === Routes ===

@router.get("/")
async def list_images_route(limit: int = 20):
    """List locally stored/generated images."""
    return JSONResponse(content={"object": "list", "data": list_images(limit)})


@router.post("/generations")
async def generate_image(
    prompt: str = Form(...),
    model: str = Form("gpt-image-1"),
    size: str = Form("1024x1024"),
    n: int = Form(1),
    background: Optional[str] = Form(None)
):
    """
    Generate images via relay (/v1/images/generations) and store locally.
    Uses unified responses toolset if available.
    """
    try:
        relay_resp = await forward_openai(
            path="/v1/images/generations",
            method="POST",
            json={"model": model, "prompt": prompt, "size": size, "n": n},
        )

        if not relay_resp or "data" not in relay_resp:
            raise HTTPException(status_code=502, detail="Relay did not return image data")

        local_paths = []
        for idx, img in enumerate(relay_resp["data"]):
            img_b64 = img.get("b64_json")
            if not img_b64:
                continue
            binary_data = io.BytesIO(bytes.fromhex(img_b64.encode("utf-8").hex()))
            file_name = f"{uuid.uuid4()}.png"
            file_path = os.path.join(IMAGES_DIR, file_name)
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(binary_data.read())
            save_metadata(prompt, model, file_path, img.get("url"))
            local_paths.append(file_path)

        return JSONResponse(
            content={
                "object": "list",
                "created": int(time.time()),
                "data": [{"object": "image", "local_path": p} for p in local_paths],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")


@router.post("/edits")
async def edit_image(
    image: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    mask: Optional[UploadFile] = File(None),
    model: str = Form("gpt-image-1"),
    size: str = Form("1024x1024"),
):
    """Edit an existing image with optional mask using relay passthrough."""
    try:
        relay_resp = await forward_openai(
            path="/v1/images/edits",
            method="POST",
            files={
                "image": (image.filename, await image.read()),
                **({"mask": (mask.filename, await mask.read())} if mask else {}),
            },
            data={"prompt": prompt or "Edit image", "model": model, "size": size},
        )
        if not relay_resp or "data" not in relay_resp:
            raise HTTPException(status_code=502, detail="Relay did not return image data")

        img_b64 = relay_resp["data"][0].get("b64_json")
        binary_data = io.BytesIO(bytes.fromhex(img_b64.encode("utf-8").hex()))
        file_name = f"edit_{uuid.uuid4()}.png"
        file_path = os.path.join(IMAGES_DIR, file_name)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(binary_data.read())
        save_metadata(prompt or "edit", model, file_path, None)
        return JSONResponse(
            content={"object": "image", "local_path": file_path, "model": model, "edited": True}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image edit failed: {e}")


@router.get("/{image_id}/content")
async def get_image_content(image_id: str):
    """Retrieve an image file as binary stream by ID."""
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute("SELECT file_path FROM images WHERE id = ?", (image_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Image not found")

    file_path = row[0]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Local image missing")

    async def stream_image():
        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(8192):
                yield chunk

    return StreamingResponse(stream_image(), media_type="image/png")


@router.delete("/{image_id}")
async def delete_image(image_id: str):
    """Delete local image and remove metadata."""
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute("SELECT file_path FROM images WHERE id = ?", (image_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Image not found")
        file_path = row[0]
        db.execute("DELETE FROM images WHERE id = ?", (image_id,))
        db.commit()

    if os.path.exists(file_path):
        os.remove(file_path)

    return JSONResponse(content={"deleted": image_id, "object": "image"})


# === Tool interface for unified /v1/responses calls ===
async def execute_image_tool(tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool entrypoint for image generation/editing inside /v1/responses.
    Example:
      { "type": "image_generation", "parameters": {"prompt": "..."} }
    """
    try:
        params = tool.get("parameters", {})
        prompt = params.get("prompt", "A simple abstract illustration")
        model = params.get("model", "gpt-image-1")
        size = params.get("size", "1024x1024")

        resp = await forward_openai(
            path="/v1/images/generations",
            method="POST",
            json={"model": model, "prompt": prompt, "size": size},
        )
        if not resp or "data" not in resp:
            return {"error": "Relay did not return image data"}

        url = resp["data"][0].get("url")
        save_metadata(prompt, model, "(remote)", url)
        return {"type": "image_generation", "url": url, "model": model}
    except Exception as e:
        return {"error": str(e)}
