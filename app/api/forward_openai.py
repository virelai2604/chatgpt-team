# ================================================================
# forward_openai.py — SDK-Aligned Passthrough Proxy
# ================================================================

import os, time, httpx, logging
from typing import Dict, Any
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse

logger = logging.getLogger("relay")

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID   = os.getenv("OPENAI_ORG_ID")
RELAY_TIMEOUT   = float(os.getenv("RELAY_TIMEOUT", 120))

# ------------------------------------------------
def _build_headers(incoming: Dict[str, str]) -> Dict[str, str]:
    """Mirror incoming headers, inject auth, remove duplicates."""
    h = dict(incoming)
    h.pop("host", None)
    h["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    if OPENAI_ORG_ID:
        h["OpenAI-Organization"] = OPENAI_ORG_ID
    return h

# ------------------------------------------------
async def forward_to_openai(request: Request, path: str) -> Any:
    """Forwards any HTTP verb to OpenAI’s upstream endpoint."""
    method = request.method.lower()
    url = f"{OPENAI_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = _build_headers(request.headers)

    # ---- Body or form data
    ctype = headers.get("content-type", "").lower()
    kwargs = {}
    if "multipart/form-data" in ctype:
        form = await request.form()
        data, files = {}, []
        for k, v in form.multi_items():
            if getattr(v, "filename", None):
                files.append((k, (v.filename, v.file, v.content_type)))
            else:
                data[k] = v
        kwargs.update(data=data, files=files)
    else:
        kwargs["content"] = await request.body()

    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT, follow_redirects=True) as client:
        try:
            logger.info(f"🔁 {method.upper()} {url}")
            resp = await client.request(method, url, headers=headers, **kwargs)
        except httpx.RequestError as e:
            logger.error(f"❌ Network error contacting OpenAI: {e}")
            return JSONResponse(
                {"error": {
                    "message": str(e),
                    "type": "network_error",
                    "param": None,
                    "code": "request_failed"
                }},
                status_code=502,
            )

    elapsed = (time.perf_counter() - start) * 1000
    logger.info(f"✅ {resp.status_code} from OpenAI in {elapsed:.1f} ms")

    ctype = resp.headers.get("content-type", "")
    if ctype.startswith("text/event-stream"):
        async def gen():
            async for chunk in resp.aiter_bytes():
                yield chunk
        return StreamingResponse(gen(), media_type="text/event-stream")

    if ctype.startswith("application/json"):
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            pass

    # Non-JSON (binary, text, etc.)
    return JSONResponse(
        {
            "object": "proxy_response",
            "status": resp.status_code,
            "content_type": ctype,
            "body": getattr(resp, "text", "")[:2000],
        },
        status_code=resp.status_code,
    )
