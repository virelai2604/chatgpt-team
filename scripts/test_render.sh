#!/usr/bin/env bash
set -euo pipefail

: "${RELAY_BASE_URL:?Set RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com}"
: "${RELAY_TOKEN:?Set RELAY_TOKEN to your Render relay token}"

export RELAY_KEY="${RELAY_KEY:-$RELAY_TOKEN}"
export INTEGRATION_OPENAI_API_KEY="${INTEGRATION_OPENAI_API_KEY:-1}"

pytest -m integration -vv \
  tests/test_success_gates_integration.py \
  tests/test_extended_routes_smoke_integration.py \
  tests/test_remaining_routes_smoke_integration.py \
  tests/test_files_and_batches_integration.py
