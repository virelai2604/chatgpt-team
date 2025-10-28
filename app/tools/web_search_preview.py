TOOL_SCHEMA = {
    "name": "web_search",
    "description": "Perform a real-time web search and return the top results.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "default": 5}
        },
        "required": ["query"]
    },
    "returns": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "url": {"type": "string"},
                "snippet": {"type": "string"}
            }
        }
    }
}
