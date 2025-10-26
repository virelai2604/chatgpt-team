# app/routes/__init__.py — BIFL v2.3.4-fp
import importlib, pkgutil
from fastapi import FastAPI

def register_routes(app: FastAPI):
    """Auto-import and register all routers under app.routes."""
    package = __package__
    for _, mod_name, _ in pkgutil.iter_modules(__path__):
        if mod_name.startswith("__"): continue
        module = importlib.import_module(f"{package}.{mod_name}")
        if hasattr(module, "router"):
            app.include_router(module.router)
            print(f"[BIFL] Registered router: {mod_name}")
