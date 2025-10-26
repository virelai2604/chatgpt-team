# ==========================================================
#  app/routes/__init__.py — BIFL v2.3.3-p2
# ==========================================================
#  Unified router loader for the ChatGPT-Team relay.
#  Automatically discovers and registers all API routes
#  located under app/routes/*.py
#
#  Features:
#   • Dynamic import and auto-registration
#   • Hybrid tool + realtime router detection
#   • Circular import safety
#   • Consistent logging output
# ==========================================================

from fastapi import FastAPI
import importlib
import pkgutil
import logging

logger = logging.getLogger("bifl.routes")

# ──────────────────────────────────────────────
#  Route Registration
# ──────────────────────────────────────────────
def register_routes(app: FastAPI):
    """
    Auto-import and register all FastAPI routers under app.routes.
    Detects any module containing a `router` variable and attaches it
    to the main FastAPI application instance.
    """

    package = __name__
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        # Skip internal or cache dirs
        if module_name.startswith("__") or module_name.startswith("services"):
            continue

        try:
            # Dynamically import the route module
            mod = importlib.import_module(f"{package}.{module_name}")

            # Only attach if it defines a router
            if hasattr(mod, "router"):
                app.include_router(mod.router)
                logger.info(f"[BIFL] Registered router: {module_name}")

            # Support optional hybrid tools router
            elif hasattr(mod, "tools_router"):
                app.include_router(mod.tools_router)
                logger.info(f"[BIFL] Registered hybrid tools router.")

            # Support realtime router (future-ready)
            elif hasattr(mod, "realtime_router"):
                app.include_router(mod.realtime_router)
                logger.info(f"[BIFL] Registered realtime router.")

        except Exception as e:
            logger.warning(f"[BIFL:WARN] Skipped router '{module_name}': {e}")

    logger.info("[BIFL] Route registration complete.")

# ==========================================================
#  End of __init__.py
# ==========================================================
