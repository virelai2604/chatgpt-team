from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from starlette.responses import JSONResponse


class ErrorDetail(BaseModel):
    message: str = Field(..., description="Human-readable error message.")
    type: str = Field(default="invalid_request_error", description="Error type.")
    param: Optional[str] = Field(default=None, description="Parameter related to the error, if any.")
    code: Optional[str] = Field(default=None, description="Machine-readable error code, if any.")


class ErrorResponse(BaseModel):
    error: ErrorDetail

    @classmethod
    def from_message(
        cls,
        message: str,
        *,
        type: str = "invalid_request_error",
        param: Optional[str] = None,
        code: Optional[str] = None,
    ) -> "ErrorResponse":
        return cls(error=ErrorDetail(message=message, type=type, param=param, code=code))

    def to_response(self, status_code: int = 400, headers: Optional[Dict[str, str]] = None) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content=self.model_dump(exclude_none=True),
            headers=headers,
        )
