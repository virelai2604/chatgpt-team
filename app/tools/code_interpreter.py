"""
app/tools/code_interpreter.py
Simulated code execution / analysis engine.
Provides lightweight sandbox execution for Python snippets.
"""

import io
import contextlib
import asyncio

async def run_code(params: dict):
    code = params.get("code", "")
    if not code:
        return {"error": "No code provided."}

    # Capture stdout safely
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(code, {})
        output = buffer.getvalue().strip() or "No output."
    except Exception as e:
        output = f"Error: {e}"
    finally:
        buffer.close()

    await asyncio.sleep(0.1)
    return {"output": output}
"""
app/tools/code_interpreter.py
Simulated code execution / analysis engine.
Provides lightweight sandbox execution for Python snippets.
"""

import io
import contextlib
import asyncio

async def run_code(params: dict):
    code = params.get("code", "")
    if not code:
        return {"error": "No code provided."}

    # Capture stdout safely
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(code, {})
        output = buffer.getvalue().strip() or "No output."
    except Exception as e:
        output = f"Error: {e}"
    finally:
        buffer.close()

    await asyncio.sleep(0.1)
    return {"output": output}
