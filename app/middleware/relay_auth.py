 from __future__ import annotations
 
 """Relay authentication middleware for the ChatGPT Team relay app."""
 
 from fastapi import HTTPException, Request
 from fastapi.responses import JSONResponse
 from starlette.middleware.base import BaseHTTPMiddleware
 from starlette.types import ASGIApp
 
 from app.utils.authy import check_relay_key
 
 __all__ = ["RelayAuthMiddleware"]
 
 class RelayAuthMiddleware(BaseHTTPMiddleware):
     """
     Enforce a relay Authorization header on `/v1/*` and `/relay/*` endpoints
     while keeping health checks open to unauthenticated probes.
     """
 
 
     def __init__(self, app: ASGIApp, *, relay_key: str) -> None:
         super().__init__(app)
         self.relay_key = relay_key
 
     async def dispatch(self, request: Request, call_next):
         # Normalize to treat trailing slashes as equivalent for routing decisions.
         path = request.url.path.rstrip("/") or "/
         
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