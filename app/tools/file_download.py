TOOL_ID = "file_download"
TOOL_VERSION = "v1"
TOOL_TYPE = "files"
TOOL_DESCRIPTION = "Download a file’s content by ID."

TOOL_SCHEMA = {
    "name": "file_download",
    "description": "Retrieve stored file contents.",
    "parameters": {
        "type": "object",
        "properties": {"file_id": {"type": "string"}},
        "required": ["file_id"]
    },
    "returns": {"type": "object", "properties": {
        "file_id": {"type": "string"}, "content": {"type": "string"}}}
}

def run(payload):
    file_id = payload.get("file_id", "unknown")
    return {"file_id": file_id, "content": "Mock file data."}
