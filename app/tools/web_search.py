TOOL_ID = "web_search"
TOOL_VERSION = "v1"
TOOL_TYPE = "web_search"
TOOL_SCHEMA = {
    "name": "web_search",
    "description": "Perform a live web search using OpenAI Search or external sources.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query text."},
            "max_results": {"type": "integer", "default": 5}
        },
        "required": ["query"]
    },
    "returns": {"type": "array", "items": {"type": "object", "properties": {
        "title": {"type": "string"}, "url": {"type": "string"}, "snippet": {"type": "string"}}}}
}
