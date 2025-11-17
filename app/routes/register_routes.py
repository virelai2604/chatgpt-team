from fastapi import FastAPI

from .actions import router as actions_router
from .conversations import router as conversations_router
from .embeddings import router as embeddings_router
from .files import router as files_router
from .images import router as images_router
from .models import router as models_router
from .realtime import router as realtime_router
from .responses import router as responses_router
from .vector_stores import router as vector_stores_router
from .videos import router as videos_router


def register_routes(app: FastAPI) -> None:
    """
    Register all versioned API routes under /v1.

    The individual routers define their own prefixes, tags, and
    OpenAI-compatible path structures so that both:
      - openai-python (2.8.0)
      - openai-node (6.9.x)

    can use this relay by simply pointing base_url at it.
    """
    app.include_router(actions_router)
    app.include_router(conversations_router)
    app.include_router(embeddings_router)
    app.include_router(files_router)
    app.include_router(images_router)
    app.include_router(models_router)
    app.include_router(realtime_router)
    app.include_router(responses_router)
    app.include_router(vector_stores_router)
    app.include_router(videos_router)
