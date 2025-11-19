#!/usr/bin/env bash
set -euo pipefail

# Go to repo root (handles spaces in path)
cd "/mnt/c/Tools/ChatGpt Domain/Cloudflare/chatgpt-team"

# Activate venv
source .venv/bin/activate

# -----------------------------
# Core runtime / environment
# -----------------------------
export APP_MODE=local
export ENVIRONMENT=local
export RELAY_NAME="ChatGPT Team Relay (local)"

# Make imports like "from app.main import app" work
export PYTHONPATH=.

# -----------------------------
# Upstream OpenAI config
# IMPORTANT:
#  - DO NOT hard-code the key in this file.
#  - Provide OPENAI_API_KEY from your shell before running this script.
# -----------------------------
export OPENAI_API_BASE="https://api.openai.com"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export OPENAI_ORG_ID=""
export DEFAULT_MODEL="gpt-4o-mini"

# -----------------------------
# Relay behavior toggles
# -----------------------------
export CHAIN_WAIT_MODE=true
export ENABLE_STREAM=true
export RELAY_TIMEOUT=120
export PROXY_TIMEOUT=120

# -----------------------------
# Tools + schema paths
# -----------------------------
export TOOLS_MANIFEST="app/manifests/tools_manifest.json"
export VALIDATION_SCHEMA_PATH="ChatGPT-API_reference_ground_truth-2025-10-29.pdf"

# -----------------------------
# Logging for debug
# -----------------------------
export LOG_LEVEL=debug
export LOG_FORMAT=json
export LOG_COLOR=false

echo "[run] Starting uvicorn on http://0.0.0.0:8000 ..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload