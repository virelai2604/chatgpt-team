"""
print_component_map.py

Utility: print key relay components and their file locations,
based on the current project tree for chatgpt-team.
"""

from pathlib import Path

# Assume this script lives in the repo root.
# Your previous run showed everything as [MISSING] because ROOT
# was set to parents[1] (one level above the repo).
ROOT = Path(__file__).resolve().parent


COMPONENTS = {
    "core_app": [
        ("app/main.py", "FastAPI app factory + middleware wiring"),
        ("app/core/config.py", "Central Settings (env-based configuration)"),
        ("app/middleware/p4_orchestrator.py", "P4 orchestrator (AsyncOpenAI client + config on request.state)"),
        ("app/middleware/relay_auth.py", "Relay key auth (protects /v1/*)"),
        ("app/middleware/validation.py", "Validation middleware against API reference PDF"),
    ],
    "forward_api": [
        ("app/api/forward_openai.py", "Single OpenAI proxy (Forward API)"),
        ("app/routes/register_routes.py", "Registers all routers and (optionally) catch-all /v1 forwarder"),
    ],
    "tools_system": [
        ("app/manifests/tools_manifest.json", "Tool definitions (web_search, code_interpreter, etc.)"),
        ("app/api/tools_api.py", "Tools discovery API: GET /v1/tools"),
    ],
    "routes_core": [
        ("app/routes/health.py", "Health endpoints: /health, /v1/health"),
        ("app/routes/actions.py", "Actions & relay info: /v1/actions/*"),
        ("app/routes/responses.py", "Chat/Responses API: /v1/responses"),
        ("app/routes/embeddings.py", "Embeddings: /v1/embeddings"),
        ("app/routes/vector_stores.py", "Vector stores API: /v1/vector_stores/*"),
        ("app/routes/files.py", "Files API: /v1/files/*"),
        ("app/routes/images.py", "Images API: /v1/images/*"),
        ("app/routes/videos.py", "Videos API: /v1/videos/*"),
        ("app/routes/models.py", "Models API: /v1/models"),
        ("app/routes/conversations.py", "Conversation history endpoints"),
        ("app/routes/realtime.py", "Realtime sessions & websocket bridge"),
    ],
    "static_and_schemas": [
        ("schemas/openapi.yaml", "OpenAPI spec used by ChatGPT Action"),
        ("static/.well-known/ai-plugin.json", "ChatGPT Action manifest"),
        ("docs/README.md", "Project documentation"),
        ("project-tree.md", "Generated project tree overview"),
    ],
    "data_and_logs": [
        ("data/conversations/conversations.db", "Conversation DB"),
        ("data/embeddings/embeddings.db", "Embeddings DB"),
        ("data/vector_stores/vectors.db", "Vector store DB"),
        ("data/files/files.db", "Files DB"),
        ("data/uploads/attachments.db", "Upload attachments DB"),
        ("logs", "Log files directory"),
    ],
    "tests": [
        ("tests/test_health_and_tools.py", "Tests health + tools routes"),
        ("tests/test_tools_and_actions_routes.py", "Tests tools and actions"),
        ("tests/test_responses_and_conversations.py", "Tests /v1/responses + conversations"),
        ("tests/test_responses_and_embeddings_sdk.py", "SDK tests for Responses + Embeddings"),
        ("tests/test_responses_stream_http.py", "Streaming responses tests"),
        ("tests/test_files_and_vectorstores.py", "Files + vector stores tests"),
        ("tests/test_models_files_vectorstores_sdk.py", "SDK tests for models, files, vector stores"),
        ("tests/test_models_files_videos_extra_routes.py", "Extra tests for models/files/videos"),
        ("tests/test_embeddings_images_videos.py", "Embeddings + images + videos tests"),
        ("tests/test_images_and_videos_routes_extra.py", "Extra image/video route tests"),
        ("tests/test_realtime_and_infra.py", "Realtime + infra tests"),
        ("tests/test_responses_stream_http.py", "HTTP streaming tests for /v1/responses"),
        ("tests/test_routes_forwarding_smoke.py", "Forwarding smoke tests"),
        ("tests/test_validation_middleware.py", "Validation middleware tests"),
        ("tests/test_videos_realtime_tools_agentic.py", "Agentic tests (videos + realtime + tools)"),
    ],
}


def main() -> None:
    print(f"Repo root: {ROOT}\n")
    for component, items in COMPONENTS.items():
        print(f"=== {component} ===")
        for rel_path, desc in items:
            path = ROOT / rel_path
            status = "OK" if path.exists() else "MISSING"
            print(f"- [{status}] {rel_path}: {desc}")
        print()


if __name__ == "__main__":
    main()
