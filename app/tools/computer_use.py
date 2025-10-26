TOOL_ID = "computer_use"
TOOL_VERSION = "v1"
TOOL_TYPE = "mcp"
TOOL_SCHEMA = {
    "name": "computer_use",
    "description": "Perform local OS actions (MCP-compliant).",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["open_file", "list_dir", "get_system_info"]},
            "path": {"type": "string"}
        },
        "required": ["action"]
    },
    "returns": {"type": "object"}
}
