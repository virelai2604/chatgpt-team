#!/usr/bin/env bash
set -euo pipefail

export RELAY_BASE_URL="${RELAY_BASE_URL:-http://localhost:8000}"
export RELAY_TOKEN="${RELAY_TOKEN:-${RELAY_KEY:-dummy}}"
export RELAY_KEY="${RELAY_KEY:-$RELAY_TOKEN}"
export INTEGRATION_OPENAI_API_KEY="${INTEGRATION_OPENAI_API_KEY:-1}"

scripts/test_success_gates_integration.py

pytest -m integration -vv \
  tests/test_extended_routes_smoke_integration.py \
  tests/test_remaining_routes_smoke_integration.py \
  tests/test_files_and_batches_integration.py
