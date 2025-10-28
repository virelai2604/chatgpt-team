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
