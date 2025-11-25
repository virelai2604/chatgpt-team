from __future__ import annotations

from fastapi import FastAPI

# Import routers from the app.routes package.
# These module names must match your actual package layout on disk:
#   app/routes/models.py
#   app/routes/embeddings.py
#   app/routes/files.py
#   app/routes/images.py
#   app/routes/videos.py
#   app/routes/vector_stores.py
#   app/routes/responses.py
#   app/routes/realtime.py
#   app/routes/conversations.py
#   app/routes/actions.py
#   app/routes/tools_api.py
from app.routes import (
    models,
    embeddings,
    files,
    images,
    videos,
    vector_stores,
    responses,
    realtime,
    conversations,
    actions,
    tools_api,
)


def register_routes(app: FastAPI) -> None:
    """
    Attach all OpenAI-compatible and relay-local routers to the app.

    All of these routers expose paths that the E2E script probes:

      Core OpenAI-style surfaces:
        - GET  /v1/models
        - GET  /v1/models/{id}
        - POST /v1/embeddings
        - GET/POST/DELETE /v1/files, /v1/files/{id}
        - POST /v1/images, /v1/images/generations, etc.
        - POST/GET /v1/videos, /v1/videos/{id}, ...
        - GET/POST /v1/vector_stores, /v1/vector_stores/{id}
        - POST/GET /v1/responses, /v1/responses/{id}, ...
        - GET/POST /v1/conversations, /v1/conversations/{id}, ...
        - POST /v1/realtime/sessions

      Relay-local surfaces:
        - GET /relay/actions
        - GET /relay/models
        - GET /v1/actions/relay_info
        - GET /v1/tools
        - GET /v1/tools/{tool_id}
    """

    # ------- Core OpenAI-proxy surfaces -------

    # /v1/models, /v1/models/{model_id}
    app.include_router(models.router)

    # /v1/embeddings
    app.include_router(embeddings.router)

    # /v1/files*, /v1/files/{file_id}
    app.include_router(files.router)

    # /v1/images*, /v1/images/...
    app.include_router(images.router)

    # /v1/videos*, /v1/videos/{id}, ...
    app.include_router(videos.router)

    # /v1/vector_stores*, /v1/vector_stores/{id}
    app.include_router(vector_stores.router)

    # /v1/responses*, streaming, cancel, etc.
    app.include_router(responses.router)

    # /v1/realtime/sessions + WebSocket upgrader
    app.include_router(realtime.router)

    # /v1/conversations*, local CSV cache, etc.
    app.include_router(conversations.router)

    # ------- Local relay info / actions --------
    # /relay/actions, /relay/models, /v1/actions/relay_info
    app.include_router(actions.router)

    # /v1/tools, /v1/tools/{tool_id}
    app.include_router(tools_api.router)
