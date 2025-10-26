TOOL_ID = "moderation"
TOOL_VERSION = "v1"
TOOL_TYPE = "safety"
TOOL_SCHEMA = {
    "name": "moderation",
    "description": "Check input for content safety violations.",
    "parameters": {
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"]
    },
    "returns": {"type": "object", "properties": {"flagged": {"type": "boolean"}, "categories": {"type": "object"}}}
}
