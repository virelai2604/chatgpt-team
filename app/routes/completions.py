# app/routes/completions.py
from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/completions")
async def completions(request: Request):
    # Dummy handler (replace with real logic as needed)
    data = await request.json()
    # For test-run, just echo the input
    return {"choices": [{"text": "Hello, world!", "finish_reason": "stop"}]}
