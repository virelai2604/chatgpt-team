 # app/middleware/relay_auth.py
 
 from __future__ import annotations
 
 from fastapi import HTTPException, Request
 from fastapi.responses import JSONResponse
 from starlette.middleware.base import BaseHTTPMiddleware
 from starlette.types import ASGIApp
 
 from app.utils.authy import check_relay_key
 
 
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
 
         # Only protect relay-facing paths; health endpoints remain open.
         protected_path = path.startswith(("/v1", "/relay"))
         health_path = path in {"/health", "/v1/health"}

         if protected_path and not health_path:
             auth_header = request.headers.get("Authorization")
             try:
                 check_relay_key(auth_header)
             except HTTPException as exc:
                 return JSONResponse(
                     status_code=exc.status_code,
                     content={"detail": exc.detail},
                     headers=exc.headers,
                 )
 
         return await call_next(request)
