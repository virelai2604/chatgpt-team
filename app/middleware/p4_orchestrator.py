# ================================================================
# p4_orchestrator.py — Pipeline Orchestrator Middleware
# ================================================================
# This middleware coordinates API requests and enforces consistency
# across routes. It acts as the "preflight" logic layer, ensuring
# every request follows the same lifecycle:
#   1. Log and timestamp
#   2. Inject metadata for traceability
#   3. Perform async validation (optional)
#   4. Forward downstream to handlers or passthrough
# ================================================================

import time
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()

        # Assign a lightweight trace ID for observability
        trace_id = f"trace_{int(start_time * 1000)}"
        request.state.trace_id = trace_id

        # Log the incoming request path and method
        print(f"[{trace_id}] {request.method} {request.url.path}")

        # Optionally validate JSON before proceeding
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                _ = await request.json()
            except Exception:
                return JSONResponse({
                    "error": {
                        "message": "Invalid or malformed JSON in request body.",
                        "type": "validation_error",
                        "trace_id": trace_id
                    }
                }, status_code=400)

        # Execute downstream handler
        response = await call_next(request)
        elapsed = (time.time() - start_time) * 1000

        # Add standard telemetry headers
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Response-Time-ms"] = f"{elapsed:.2f}"

        print(f"[{trace_id}] Completed {request.method} {request.url.path} ({elapsed:.1f} ms)")
        return response
