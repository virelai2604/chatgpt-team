"""
actions.py — Custom ChatGPT Actions Endpoints
─────────────────────────────────────────────
Expose custom APIs for ChatGPT Actions via your ai-plugin.json and openapi.yaml.
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/actions", tags=["actions"])

@router.get("/ping")
async def ping():
    """Simple health test for ChatGPT Action integration."""
    return {"status": "ok", "message": "ChatGPT Action is alive."}

@router.get("/weather")
async def get_weather(city: str = Query(..., description="City name")):
    """Example ChatGPT Action — provides mock weather data."""
    data = {
        "city": city,
        "temperature_c": 26.4,
        "conditions": "Sunny with clear skies",
        "source": "relay-weather"
    }
    return JSONResponse(data, status_code=200)

@router.post("/echo")
async def echo_action(payload: dict):
    """Echoes any JSON payload — useful for plugin debugging."""
    return JSONResponse({"echo": payload}, status_code=200)
