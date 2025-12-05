# app/routes/__init__.py

from __future__ import annotations

from fastapi import APIRouter

from .register_routes import register_routes

# Public router that aggregates all resource routers under /v1.
router = APIRouter()

# Wire up all sub‑routers (health, files, conversations, etc.).
register_routes(router)

__all__ = [
    "router",
    "register_routes",
]
