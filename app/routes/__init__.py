# ==========================================================
# app/routes/__init__.py — BIFL v2.3.4-fp
# Auto-register all FastAPI routers recursively (fixed)
# ==========================================================
import importlib
import pkgutil
from fastapi import FastAPI

def register_routes(app_instance: FastAPI):
    import app.routes as routes_pkg
    # Recursively walk through all submodules of app.routes
    for _, module_name, _ in pkgutil.walk_packages(routes_pkg.__path__, routes_pkg.__name__ + "."):
        module = importlib.import_module(module_name)
        if hasattr(module, "router"):
            app_instance.include_router(module.router)
            print(f"[BIFL] Registered router: {module_name.split('.')[-1]}")
