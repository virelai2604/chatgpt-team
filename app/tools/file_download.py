# ============================================================
# Tool: file_download — Retrieve file content
# ============================================================

import os

TOOL_SCHEMA = {
    "name": "file_download",
    "description": "Retrieve a file’s contents by its ID.",
    "parameters": {
        "type": "object",
        "properties": {"file_id": {"type": "string"}},
        "required": ["file_id"]
    },
    "returns": {
        "type": "object",
        "properties": {"file_id": {"type": "string"}, "content": {"type": "string"}}
    }
}

async def run(payload: dict) -> dict:
    """Reads a file from disk (mocked by filename as ID)."""
    file_id = payload.get("file_id", "")
    if not os.path.exists(file_id):
        return {"file_id": file_id, "content": ""}
    with open(file_id, "r", encoding="utf-8") as f:
        content = f.read()
    return {"file_id": file_id, "content": content}
