TOOL_ID = "vector_store_retrieval"
TOOL_VERSION = "v1"
TOOL_TYPE = "vector_store"
TOOL_DESCRIPTION = "Retrieve data from vector stores for RAG (retrieval-augmented generation)."

TOOL_SCHEMA = {
    "name": "vector_store_retrieval",
    "description": "Retrieve top matching documents or embeddings.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "vector_store_id": {"type": "string"},
            "top_k": {"type": "integer", "default": 3}
        },
        "required": ["query"]
    },
    "returns": {"type": "array", "items": {
        "type": "object",
        "properties": {"doc_id": {"type": "string"}, "score": {"type": "number"}, "content": {"type": "string"}}
    }}
}

def run(payload):
    query = payload.get("query", "")
    return [
        {"doc_id": f"mock_{i}", "score": 0.9 - i*0.1, "content": f"Match for '{query}' in document {i}"}
        for i in range(3)
    ]
