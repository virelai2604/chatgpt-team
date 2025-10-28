TOOL_SCHEMA = {
    "name": "code_interpreter",
    "description": "Execute Python code safely in a sandboxed environment.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute."
            },
            "timeout": {
                "type": "integer",
                "default": 10,
                "description": "Maximum seconds to allow execution."
            }
        },
        "required": ["code"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
            "result": {"type": "string"}
        }
    }
}
