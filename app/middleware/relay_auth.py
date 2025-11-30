# app/middleware/relay_auth.py


from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp




class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces a relay Authorization header on all
    `/v1/*` and `/relay/*` endpoints, but leaves `/health` public.
    """

    def __init__(self, app: ASGIApp, *, relay_key: str) -> None:
        super().__init__(app)
        self.relay_key = relay_key

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # health endpoints should remain open
        if path not in ("/health", "/v1/health"):
            auth_header = request.headers.get("Authorization")
            try:
                check_relay_key(auth_header)
            except HTTPException as exc:  # pragma: no cover - handled in tests
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail},
                    headers=exc.headers,
                )

        return await call_next(request)
