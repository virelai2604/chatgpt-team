# ============================================================
# app/routes/register_routes.py
# Dynamic route loader for BIFL relay (v2.3.4-fp)
# ============================================================

import os
import pkgutil
import importlib
import logging

logger = logging.getLogger("BIFL")


def register_routes(app):
    """
    Dynamically discover and include routers from:
      - app.api.*  (custom APIs like tools_api, responses_api)
      - app.routes.*  (core endpoints like videos, files, etc.)

    Handles namespace packages safely (no __init__.py required).
    """

    base_packages = ["app.routes", "app.api"]
    logger.info("[BIFL] Starting router auto-registration...")

    for package_name in base_packages:
        try:
            # Import package (e.g., app.api or app.routes)
            package = importlib.import_module(package_name)
            package_path = getattr(package, "__file__", None)

            # Handle namespace packages that lack __file__
            if not package_path:
                logger.warning(f"[BIFL] Skipped namespace package {package_name} (no __file__)")
                continue

            package_dir = os.path.dirname(package_path)

            # Iterate through submodules in the package
            for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
                if is_pkg:
                    continue  # Skip subfolders

                full_module_name = f"{package_name}.{module_name}"

                try:
                    module = importlib.import_module(full_module_name)

                    # Attach routers if they exist
                    if hasattr(module, "router"):
                        app.include_router(module.router)
                        prefix = getattr(module.router, "prefix", "(no prefix)")
                        logger.info(f"[BIFL] Router attached: {full_module_name} → prefix={prefix}")
                    else:
                        logger.debug(f"[BIFL] Skipped {full_module_name}: no router found")

                except Exception as e:
                    logger.warning(f"[BIFL] Failed to import {full_module_name}: {e}")

        except Exception as e:
            logger.error(f"[BIFL] Error loading package {package_name}: {e}")

    logger.info("[BIFL] Route registration complete.")
