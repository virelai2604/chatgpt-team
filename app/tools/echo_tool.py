TOOL_ID = "echo_tool"
TOOL_VERSION = "v1"
TOOL_TYPE = "function"
TOOL_DESCRIPTION = "Echoes back any provided text."

TOOL_SCHEMA = {
    "name": "echo_tool",
    "description": "Return the same text that was given.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to echo back."}
        },
        "required": ["text"]
    },
    "returns": {"type": "string", "description": "The same text that was input."}
}

def run(payload):
    text = payload.get("text", "")
    return {"echo": text}
