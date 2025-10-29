# app/api/tools_api.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import importlib
import logging

logger = logging.getLogger("relay.tools_api")
router = APIRouter(prefix="/v1/responses", tags=["tools"])

# --------------------------------------------------------
# Tool Registry (Ground Truth)
# --------------------------------------------------------
TOOL_REGISTRY = {
    "code_interpreter": {"path": "app.tools.code_interpreter"},
    "file_search": {"path": "app.tools.file_search"},
    "file_upload": {"path": "app.tools.file_upload"},
    "file_download": {"path": "app.tools.file_download"},
    "vector_store_retrieval": {"path": "app.tools.vector_store_retrieval"},
    "image_generation": {"path": "app.tools.image_generation"},
    "video_generation": {"path": "app.tools.video_generation"},
    "web_search": {"path": "app.tools.web_search"},
    "computer_use": {"path": "app.tools.computer_use"},
}

# Optional backward-compatible aliases for older clients
ALIASES = {
    "web_search_preview": "web_search",
    "computer_use_preview": "computer_use",
}


def get_tool_metadata(name: str) -> dict:
    """
    Dynamically imports a tool module and retrieves metadata.
    Falls back gracefully if module or attributes are missing.
    """
    tool_name = ALIASES.get(name, name)

    if tool_name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found")

    try:
        module_path = TOOL_REGISTRY[tool_name]["path"]
        module = importlib.import_module(module_path)
        metadata = getattr(module, "METADATA", None)
        if not metadata:
            metadata = {"name": tool_name, "description": "No metadata available."}
        return metadata
    except Exception as e:
        logger.error(f"Error loading tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load tool '{name}'")


@router.get("/tools", response_class=JSONResponse)
async def list_tools():
    """
    Returns the full list of registered relay tools.
    Mirrors OpenAI-style response for easier client compatibility.
    """
    try:
        tool_list = list(TOOL_REGISTRY.keys())
        return JSONResponse(
            {
                "object": "list",
                "tools": tool_list,
                "count": len(tool_list),
                "registry_version": "1.0",
            }
        )
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{tool_name}", response_class=JSONResponse)
async def get_tool(tool_name: str):
    """
    Retrieve metadata for a specific tool.
    Useful for debugging and manifest validation.
    """
    metadata = get_tool_metadata(tool_name)
    return JSONResponse(metadata)


# --------------------------------------------------------
# End of tools_api.py
# --------------------------------------------------------
