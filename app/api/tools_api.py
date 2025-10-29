# ==========================================================
# app/api/tools_api.py — Tool Registry and Metadata
# ==========================================================
# Defines all available relay tools and their metadata.
# Used by /v1/responses/tools and /v1/relay/status endpoints.
# ==========================================================

from fastapi import APIRouter

router = APIRouter(prefix="/v1/responses", tags=["tools"])

# ✅  TOOL REGISTRY — the single source of truth
TOOL_REGISTRY = [
    {"id": "code_interpreter",
     "name": "Code Interpreter",
     "description": "Run Python code safely in a sandboxed environment."},
    {"id": "file_search",
     "name": "File Search",
     "description": "Search inside uploaded documents or files."},
    {"id": "file_upload",
     "name": "File Upload",
     "description": "Upload a file to the relay for later use."},
    {"id": "file_download",
     "name": "File Download",
     "description": "Download a stored or generated file by ID."},
    {"id": "vector_store_retrieval",
     "name": "Vector Store Retrieval",
     "description": "Retrieve embeddings or semantic search from the vector store."},
    {"id": "image_generation",
     "name": "Image Generation",
     "description": "Generate an image from a prompt or modify an existing one."},
    {"id": "web_search",
     "name": "Web Search",
     "description": "Perform a live web search using trusted sources."},
    {"id": "video_generation",
     "name": "Video Generation",
     "description": "Generate or edit short video clips from text prompts."},
    {"id": "computer_use",
     "name": "Computer Use",
     "description": "Control a simulated desktop environment for automation tasks."}
]

@router.get("/tools")
async def list_tools():
    """Return the available tool registry in OpenAI-style schema."""
    return {"object": "list", "tools": [t["id"] for t in TOOL_REGISTRY]}
