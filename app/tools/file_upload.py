# ============================================================
# Tool: file_upload — Stores mock file content
# ============================================================

import os, time, uuid

TOOL_SCHEMA = {
    "name": "file_upload",
    "description": "Upload a file and return metadata for later use.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "content": {"type": "string", "description": "Base64 or plain file data."}
        },
        "required": ["filename", "content"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "object": {"type": "string"},
            "created_at": {"type": "string"},
            "filename": {"type": "string"}
        }
    }
}

async def run(payload: dict) -> dict:
    """Stores file locally and returns metadata."""
    file_id = str(uuid.uuid4())
    filename = payload.get("filename", "file.txt")
    content = payload.get("content", "")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return {
        "id": file_id,
        "object": "file",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "filename": filename
    }
