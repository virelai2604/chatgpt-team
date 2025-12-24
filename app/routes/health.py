# app/routes/health.py

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


def _payload() -> dict:
    return {"status": "ok"}


@router.get("/", summary="Root health check")
async def root_health() -> dict:
    # Test suite expects GET / to return 200 with {"status": "ok"}.
    return _payload()


@router.get("/health", summary="Health check")
async def health() -> dict:
    return _payload()


@router.get("/v1/health", summary="Health check (v1)")
async def v1_health() -> dict:
    return _payload()
