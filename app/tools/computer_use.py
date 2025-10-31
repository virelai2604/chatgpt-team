"""
app/tools/computer_use.py
Simulated computer interaction tool (Ground Truth placeholder).
Used for file creation, environment introspection, etc.
"""

import os
import asyncio

async def perform_action(params: dict):
    action = params.get("action", "inspect")
    path = params.get("path", ".")

    if action == "list_files":
        try:
            files = os.listdir(path)
        except Exception as e:
            return {"error": str(e)}
        return {"path": path, "files": files}

    if action == "get_env":
        return {"environment": dict(os.environ)}

    await asyncio.sleep(0.1)
    return {"message": f"Performed {action} successfully."}
