from app.routes.services.tool_registry import register_tool
import sympy as sp

@register_tool("math_solver")
async def math_solver(expression: str):
    """Solve symbolic math expressions."""
    try:
        expr = sp.sympify(expression)
        result = sp.simplify(expr)
        return {"expression": expression, "result": str(result)}
    except Exception as e:
        return {"error": str(e)}
