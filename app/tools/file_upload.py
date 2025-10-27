import uuid
import datetime

TOOL_ID = "file_upload"
TOOL_VERSION = "v1"
TOOL_TYPE = "files"
TOOL_DESCRIPTION = "Upload files from within tool calls, returning file metadata."

TOOL_SCHEMA = {
    "name": "file_upload",
    "description": "Upload files for later use by tools or models.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "content": {"type": "string", "description": "Base64 or plain content."}
        },
        "required": ["filename", "content"]
    },
    "returns": {"type": "object", "properties": {
        "id": {"type": "string"}, "object": {"type": "string"}, "created_at": {"type": "string"} }}
}

def run(payload):
    filename = payload.get("filename")
    return {
        "id": f"file_{uuid.uuid4()}",
        "object": "file",
        "created_at": datetime.datetime.utcnow().isoformat(),
        "filename": filename,
        "status": "uploaded"
    }
