# ==========================================================
# app/routes/__init__.py — BIFL v2.3.4-fp
# Auto-register all FastAPI routers recursively
# ==========================================================
import importlib
import pkgutil
from fastapi import FastAPI

def register_routes(app: FastAPI):
    import app.routes
    # Recursively walk through all submodules of app.routes
    for _, module_name, _ in pkgutil.walk_packages(app.routes.__path__, app.routes.__name__ + "."):
        module = importlib.import_module(module_name)
        if hasattr(module, "router"):
            app.include_router(module.router)
            print(f"[BIFL] Registered router: {module_name.split('.')[-1]}")
