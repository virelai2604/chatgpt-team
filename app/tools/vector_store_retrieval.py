# ============================================================
# Tool: vector_store_retrieval — Retrieve top matches mock
# ============================================================

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

async def run(payload: dict) -> list:
    """Simulates a vector retrieval."""
    q = payload.get("query", "")
    k = int(payload.get("top_k", 3))
    return [{"doc_id": f"doc_{i}", "score": 0.95 - 0.1 * i, "content": f"Match for '{q}'"} for i in range(k)]
