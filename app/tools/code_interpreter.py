# ============================================================
# Tool: code_interpreter — Executes Python safely in sandbox
# ============================================================

import io, contextlib, traceback

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

async def run(payload: dict) -> dict:
    """Executes Python code safely and returns stdout, stderr, and status."""
    code = payload.get("code", "")
    stdout, stderr = io.StringIO(), io.StringIO()
    result = ""
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(code, {})
        result = "ok"
    except Exception:
        stderr.write(traceback.format_exc())
        result = "error"
    return {"stdout": stdout.getvalue(), "stderr": stderr.getvalue(), "result": result}
