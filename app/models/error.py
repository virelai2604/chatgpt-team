from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field
from starlette.responses import JSONResponse, Response


class ErrorResponse(BaseModel):
    """
    Small, reusable error envelope used by middleware and (optionally) routes.

    Ground-truth requirement:
      - Must exist at `app.models.error`
      - Must support `ErrorResponse(detail=...).to_response(status_code=...)`
    """

    detail: str = Field(..., description="Human-readable error detail.")

    def to_response(self, *, status_code: int) -> Response:
        payload: Dict[str, Any]
        # Pydantic v2: model_dump(); v1: dict()
        if hasattr(self, "model_dump"):
            payload = self.model_dump()  # type: ignore[attr-defined]
        else:
            payload = self.dict()  # type: ignore[call-arg]
        return JSONResponse(status_code=status_code, content=payload)
