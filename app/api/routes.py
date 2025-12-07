# app/api/routes.py

from __future__ import annotations

from fastapi import APIRouter

from app.routes.register_routes import register_routes
from app.utils.logger import get_logger

logger = get_logger(__name__)

# This router is included by app.main and mirrors all route families under /v1.
router = APIRouter()

# Delegate wiring to the shared register_routes helper.
register_routes(router)

logger.info("API router initialized with shared route families")
