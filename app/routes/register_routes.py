# ============================================================
# app/routes/register_routes.py — Unified Route Loader
# Automatically registers all routers from app.api & app.routes
# ============================================================

import os
import pkgutil
import importlib
import logging
from fastapi import FastAPI

logger = logging.getLogger("BIFL.RegisterRoutes")

def register_routes(app: FastAPI):
    """
    Dynamically discover and include routers from:
      - app.api.*  (tools_api, responses, passthrough_proxy)
      - app.routes.*  (audio, images, vector_stores, etc.)
    """
    base_packages = ["app.api", "app.routes"]
    logger.info("[BIFL] Starting router auto-registration...")

    for package_name in base_packages:
        try:
            package = importlib.import_module(package_name)
            package_dir = os.path.dirname(package.__file__)

            for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
                if is_pkg:
                    continue
                full_module = f"{package_name}.{module_name}"

                try:
                    module = importlib.import_module(full_module)

                    if hasattr(module, "router"):
                        app.include_router(module.router)
                        prefix = getattr(module.router, "prefix", "")
                        logger.info(f"[BIFL] Router registered: {full_module} → prefix={prefix}")
                except Exception as e:
                    logger.warning(f"[BIFL] Skipped {full_module}: {e}")
        except Exception as e:
            logger.error(f"[BIFL] Error scanning package {package_name}: {e}")

    logger.info("[BIFL] Route registration complete.")
