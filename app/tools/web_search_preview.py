import datetime

TOOL_ID = "web_search"
TOOL_VERSION = "v1"
TOOL_TYPE = "web_search"
TOOL_DESCRIPTION = "Perform a live web search using OpenAI Search or external sources."

TOOL_SCHEMA = {
    "name": "web_search",
    "description": "Search the web for real-time information.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query text."},
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

def run(payload):
    query = payload.get("query", "")
    max_results = int(payload.get("max_results", 5))
    # mock results (for demo — replace with real API later)
    return [
        {
            "title": f"Result {i+1} for {query}",
            "url": f"https://example.com/{query.replace(' ', '_')}/{i+1}",
            "snippet": f"Generated at {datetime.datetime.utcnow()} UTC"
        }
        for i in range(max_results)
    ]
def run(payload):
    query = payload.get("query", "")
    max_results = int(payload.get("max_results", 5))
    import datetime
    return [
        {
            "title": f"Result {i+1} for {query}",
            "url": f"https://example.com/{query.replace(' ', '_')}/{i+1}",
            "snippet": f"Generated at {datetime.datetime.utcnow()} UTC"
        }
        for i in range(max_results)
    ]
