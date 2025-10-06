from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/generations", methods=["POST"])
async def image_generations(request: Request):
    return await forward_openai(request, "images/generations")

@router.api_route("/edits", methods=["POST"])
async def image_edits(request: Request):
    return await forward_openai(request, "images/edits")

@router.api_route("/variations", methods=["POST"])
async def image_variations(request: Request):
    return await forward_openai(request, "images/variations")
