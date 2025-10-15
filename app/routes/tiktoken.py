from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.utils.db_logger import save_raw_request
import tiktoken
import traceback

router = APIRouter(prefix="/v1/tokens", tags=["Tokens"])

class TokenCountInput(BaseModel):
    model: str
    text: str | None = None
    messages: list | None = None

@router.post("/count")
async def count_tokens(request: Request, input_data: TokenCountInput):
    """
    BIFL-grade: Count tokens for a text or chat message array.
    Logs every request and gracefully handles all errors.
    """
    try:
        # Log request
        body = await request.body()
        headers_json = str(dict(request.headers))
        save_raw_request(endpoint="/v1/tokens/count", raw_body=body, headers_json=headers_json)

        # Tokenize
        enc = tiktoken.encoding_for_model(input_data.model)
        total_tokens = 0

        if input_data.text:
            total_tokens = len(enc.encode(input_data.text))
        elif input_data.messages:
            for msg in input_data.messages:
                total_tokens += len(enc.encode(msg.get("role", "")))
                total_tokens += len(enc.encode(msg.get("content", "")))

        return {
            "model": input_data.model,
            "total_tokens": total_tokens
        }

    except Exception as e:
        print("[BIFL] Token Count Error:", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "token_count_error",
                    "message": str(e)
                }
            }
        )
