from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Minimal OpenAI-style error envelope used by middleware and routes.

    This is intentionally small and stable:
      - middleware constructs ErrorResponse(detail="...")
      - middleware returns err.to_response(status_code=...)
    """

    detail: str = Field(..., description="Human-readable error message")
    type: str = Field(default="invalid_request_error", description="OpenAI-style error type")
    param: Optional[str] = Field(default=None, description="Parameter name (if applicable)")
    code: Optional[str] = Field(default=None, description="Machine-readable error code (if applicable)")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "message": self.detail,
                "type": self.type,
                "param": self.param,
                "code": self.code,
            }
        }

    def to_response(self, *, status_code: int) -> JSONResponse:
        return JSONResponse(status_code=status_code, content=self.to_dict())
