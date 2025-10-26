TOOL_ID = "file_search"
TOOL_VERSION = "v2"
TOOL_TYPE = "file_search"
TOOL_SCHEMA = {
    "name": "file_search",
    "description": "Perform semantic search within uploaded files or vector stores.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "vector_store_id": {"type": "string"},
            "top_k": {"type": "integer", "default": 3}
        },
        "required": ["query"]
    },
    "returns": {"type": "array", "items": {"type": "object", "properties": {
        "filename": {"type": "string"}, "score": {"type": "number"}, "excerpt": {"type": "string"}}}}
}
