# app/api/routes.py
from fastapi import APIRouter

from . import forward_openai

# This router is mounted by app.main under / (the forward_openai router has its own prefix).
router = APIRouter()
router.include_router(forward_openai.router)
