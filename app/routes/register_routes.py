"""
register_routes.py — Centralized router registration for all /v1 relay endpoints.
"""
from rich.console import Console

# ✅ Direct submodule imports (avoids __init__.py dependencies)
from app.routes import responses
from app.routes import embeddings
from app.routes import models
from app.routes import vector_stores
from app.routes import realtime

# Optional: only import tools if the file exists
try:
    from app.routes import tools
except ImportError:
    tools = None

console = Console()

def register_routes(app):
    """Registers all route modules with the FastAPI relay app."""
    try:
        app.include_router(responses.router)
        app.include_router(embeddings.router)
        app.include_router(models.router)
        app.include_router(vector_stores.router)
        app.include_router(realtime.router)
        if tools:
            app.include_router(tools.router)

        console.print("[bold green]✅ All route modules successfully registered with FastAPI.[/bold green]")
        console.print("   - Core /v1 routes active")
        console.print("   - Tool orchestration active")
        console.print("   - Realtime streaming endpoints active")

    except Exception as e:
        console.print(f"[bold red]❌ Route registration failed:[/bold red] {e}")
        raise
