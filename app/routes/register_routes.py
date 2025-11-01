# ================================================================
# register_routes.py — Router Registry
# ================================================================
# Collects all route modules into a single mountable router.
# Ensures each route group registers under the FastAPI app.
# ================================================================

from fastapi import FastAPI
from app.routes import (
    conversations,
    embeddings,
    files,
    models,
    realtime,
    responses,
    vector_stores,
)

def register_routes(app: FastAPI):
    """
    Attach all route modules to the FastAPI instance.
    """
    routers = [
        conversations.router,
        embeddings.router,
        files.router,
        models.router,
        realtime.router,
        responses.router,
        vector_stores.router,
    ]

    for router in routers:
        app.include_router(router)

    return app
