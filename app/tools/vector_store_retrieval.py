TOOL_SCHEMA = {
    "name": "vector_store_retrieval",
    "description": "Retrieve top matching documents or embeddings from a vector store.",
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
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "doc_id": {"type": "string"},
                "score": {"type": "number"},
                "content": {"type": "string"}
            }
        }
    }
}
