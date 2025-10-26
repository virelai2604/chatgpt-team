# app/routes/services/tools_admin.py — BIFL v2.2
# Provides administrative endpoints for the tool registry and runtime management.

import os, json, importlib, uuid
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.utils.db_logger import save_raw_request
from app.utils.error_handler import error_response
from app.routes.services.tool_registry import load_tools

router = APIRouter(prefix="/v1/tools/admin", tags=["Tools Admin"])

# Runtime tool cache (dynamic reloads)
REGISTRY = {}


@router.get("/version")
async def version():
    """Return current BIFL version and tool count."""
    tools = load_tools()
    return {
        "object": "bifl_admin",
        "bifl_version": "2.2",
        "tools_count": len(tools),
        "uuid": str(uuid.uuid4())
    }


@router.get("/registry")
async def list_registered_tools():
    """List all registered tools and their source modules."""
    trace_id = str(uuid.uuid4())
    tools = load_tools()
    save_raw_request(endpoint="tools/list", raw_body="", headers_json=f'{{"trace_id":"{trace_id}"}}')

    return {
        "object": "tool_registry",
        "trace_id": trace_id,
        "count": len(tools),
        "tools": tools
    }


@router.post("/refresh")
async def refresh_tools():
    """Hot reload tools.json and dynamically import new tool functions."""
    trace_id = str(uuid.uuid4())
    tools_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "tools.json")

    if not os.path.exists(tools_path):
        return error_response(
            "not_found",
            f"tools.json not found at {tools_path}",
            404,
            {"trace_id": trace_id}
        )

    try:
        with open(tools_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        REGISTRY.clear()
        for t in (data["tools"] if "tools" in data else data):
            if not all(k in t for k in ("name", "module", "function")):
                continue
            module = importlib.import_module(t["module"])
            REGISTRY[t["name"]] = getattr(module, t["function"])

        save_raw_request(
            endpoint="tools/refresh",
            raw_body=json.dumps(data),
            headers_json=f'{{"trace_id":"{trace_id}"}}'
        )

        return {
            "object": "reload",
            "trace_id": trace_id,
            "status": "ok",
            "count": len(REGISTRY),
            "tools": list(REGISTRY.keys())
        }
    except Exception as e:
        return error_response("load_error", str(e), 500, {"trace_id": trace_id})


@router.get("/meta")
async def admin_meta():
    """Return admin diagnostics for this module."""
    return {
        "object": "tools_admin",
        "registry_count": len(REGISTRY),
        "file_origin": __file__,
        "uuid": str(uuid.uuid4())
    }
