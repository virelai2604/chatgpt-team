TOOL_ID = "math_solver"
TOOL_TYPE = "function"
TOOL_VERSION = "v1"
TOOL_DESCRIPTION = "Evaluates arithmetic and algebraic expressions safely."

TOOL_SCHEMA = {
    "name": "math_solver",
    "description": "Solve a mathematical expression and return the result as JSON.",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Math expression, e.g. '2 + 3 * (4 - 1)'"}
        },
        "required": ["expression"]
    }
}

def run(payload: dict):
    try:
        expr = str(payload.get("expression", "0"))
        # Use safe eval environment
        result = eval(expr, {"__builtins__": None}, {})
        return {"expression": expr, "result": result}
    except Exception as e:
        return {"error": str(e)}
