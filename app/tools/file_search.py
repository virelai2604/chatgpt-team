TOOL_SCHEMA = {
    "name": "file_search",
    "description": "Search uploaded files or vector stores for matching text.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "vector_store_id": {"type": "string"},
            "top_k": {"type": "integer", "default": 3}
        },
        "required": ["query"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "matches": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "score": {"type": "number"},
                        "excerpt": {"type": "string"}
                    }
                }
            }
        }
    }
}
