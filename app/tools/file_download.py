TOOL_SCHEMA = {
    "name": "file_download",
    "description": "Retrieve a file’s contents by its ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_id": {"type": "string"}
        },
        "required": ["file_id"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "file_id": {"type": "string"},
            "content": {"type": "string"}
        }
    }
}
