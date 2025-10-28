# ============================================================
# Tool: file_search — Semantic search mock
# ============================================================

import json

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

async def run(payload: dict) -> dict:
    """Performs mock semantic search across files."""
    query = payload.get("query", "")
    top_k = int(payload.get("top_k", 3))
    results = [
        {
            "filename": f"mock_doc_{i+1}.txt",
            "score": 0.9 - i * 0.1,
            "excerpt": f"Snippet showing relevance to query: '{query}'"
        }
        for i in range(top_k)
    ]
    return {"matches": results}
