# app/api/routes.py
from fastapi import APIRouter

from . import forward_openai

router = APIRouter()
router.include_router(forward_openai.router)
