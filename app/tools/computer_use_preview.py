TOOL_SCHEMA = {
    "name": "computer_use",
    "description": "Simulate or perform computer actions (GUI automation, file I/O, typing).",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "target": {"type": "string"},
            "text": {"type": "string"}
        },
        "required": ["action"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "details": {"type": "string"}
        }
    }
}
