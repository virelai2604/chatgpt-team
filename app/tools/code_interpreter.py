TOOL_ID = "code_interpreter"
TOOL_VERSION = "v2"
TOOL_TYPE = "function"
TOOL_SCHEMA = {
    "name": "code_interpreter",
    "description": "Execute Python code in a sandboxed environment.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to execute."}
        },
        "required": ["code"]
    },
    "returns": {"type": "object", "properties": {
        "stdout": {"type": "string"}, "stderr": {"type": "string"}, "result": {"type": "string"}}}
}
def run(payload):
    """Simulates /v1/code_interpreter call."""
    code = payload.get("code", "print('Hello')")
    return {
        "id": "ci_mock_001",
        "status": "completed",
        "stdout": f"Executed: {code}",
        "outputs": [{"type": "text", "content": "Hello from interpreter"}]
    }
def run(payload):
    """Simulates /v1/code_interpreter call."""
    code = payload.get("code", "print('Hello')")
    return {
        "id": "ci_mock_001",
        "status": "completed",
        "stdout": f"Executed: {code}",
        "outputs": [{"type": "text", "content": "Hello from interpreter"}]
    }
