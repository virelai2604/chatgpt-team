# ============================================================
# Tool: computer_use — Simulated OS automation
# ============================================================

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
        "properties": {"status": {"type": "string"}, "details": {"type": "string"}}
    }
}

async def run(payload: dict) -> dict:
    """Simulates computer actions (mock)."""
    action = payload.get("action", "")
    target = payload.get("target", "")
    text = payload.get("text", "")
    return {"status": "ok", "details": f"Simulated {action} on {target or 'system'} with text='{text}'"}
