"""
ChatGPT Team Relay — Vector Store Routes
----------------------------------------
Implements CRUD proxy routes for /v1/vector_stores endpoints.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter()

@router.get("/v1/vector_stores")
async def list_vector_stores():
    """GET /v1/vector_stores"""
    response = await forward_openai_request("v1/vector_stores", method="GET")
    return JSONResponse(content=response.json())

@router.post("/v1/vector_stores")
async def create_vector_store(request: Request):
    """POST /v1/vector_stores"""
    body = await request.json()
    response = await forward_openai_request("v1/vector_stores", method="POST", json=body)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return JSONResponse(content=response.json())

@router.get("/v1/vector_stores/{store_id}")
async def get_vector_store(store_id: str):
    """GET /v1/vector_stores/{store_id}"""
    response = await forward_openai_request(f"v1/vector_stores/{store_id}", method="GET")
    return JSONResponse(content=response.json())

@router.patch("/v1/vector_stores/{store_id}")
async def update_vector_store(store_id: str, request: Request):
    """PATCH /v1/vector_stores/{store_id}"""
    body = await request.json()
    response = await forward_openai_request(f"v1/vector_stores/{store_id}", method="PATCH", json=body)
    return JSONResponse(content=response.json())

@router.delete("/v1/vector_stores/{store_id}")
async def delete_vector_store(store_id: str):
    """DELETE /v1/vector_stores/{store_id}"""
    response = await forward_openai_request(f"v1/vector_stores/{store_id}", method="DELETE")
    return JSONResponse(content=response.json())
