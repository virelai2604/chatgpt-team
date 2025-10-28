# ==========================================================
# app/routes/__init__.py — Package Export Definitions
# ==========================================================
# Ensures that all route modules can be imported cleanly
# by register_routes.py or elsewhere in the relay.
# ==========================================================

from . import (
    core,
    chat,
    models,
    files,
    vector_stores,
    realtime,
    relay_status,
    openapi,
)

__all__ = [
    "core",
    "chat",
    "models",
    "files",
    "vector_stores",
    "realtime",
    "relay_status",
    "openapi",
]
