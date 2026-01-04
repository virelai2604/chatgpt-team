#!/usr/bin/env bash
set -euo pipefail

# chain_wait_routes_test.sh
#
# Sequentially exercise relay routes with optional per-request wait.
#
# Required env:
#   BASE_URL        Base URL for the relay (default: https://chatgpt-team-relay.onrender.com)
#   RELAY_KEY       Relay auth key (used for Authorization + X-Relay-Key)
#
# Optional env:
#   AUTH_HEADER     Override Authorization header (default: "Authorization: Bearer $RELAY_KEY")
#   CHAIN_WAIT_SEC  Seconds to sleep between requests (default: 0.5)
#   MODEL           Responses model (default: gpt-4.1-mini)
#   EMBED_MODEL     Embeddings model (default: text-embedding-3-small)
#   IMAGE_PROMPT    Image prompt (default: "a small robot")
#   VIDEO_PROMPT    Video prompt (default: "a cat running")
#   VIDEO_MODEL     Video model (default: sora-2)
#   RESPONSE_ID, MODEL_ID, FILE_ID, VECTOR_STORE_ID, CONVERSATION_ID,
#   UPLOAD_ID, VIDEO_JOB_ID, TOOL_ID
#   STREAM          true/false for streaming responses (default: true)
#
# Notes:
# - Endpoints that require IDs are skipped if the ID is not set.
# - Some endpoints require upstream OpenAI credentials in the relay.
# - Health endpoints are public even when relay auth is enabled.

BASE_URL="${BASE_URL:-https://chatgpt-team-relay.onrender.com}"
CHAIN_WAIT_SEC="${CHAIN_WAIT_SEC:-0.5}"
MODEL="${MODEL:-gpt-4.1-mini}"
EMBED_MODEL="${EMBED_MODEL:-text-embedding-3-small}"
IMAGE_PROMPT="${IMAGE_PROMPT:-a small robot}"
VIDEO_PROMPT="${VIDEO_PROMPT:-a cat running}"
VIDEO_MODEL="${VIDEO_MODEL:-sora-2}"
STREAM="${STREAM:-true}"

RELAY_KEY="${RELAY_KEY:-}"
AUTH_HEADER="${AUTH_HEADER:-Authorization: Bearer ${RELAY_KEY}}"
X_RELAY_HEADER="X-Relay-Key: ${RELAY_KEY}"

timestamp() {
  date +"%Y-%m-%dT%H:%M:%S%z"
}

log() {
  echo "[$(timestamp)] $*"
}

sleep_chain() {
  local wait_sec="$1"
  if [[ "${wait_sec}" != "0" && "${wait_sec}" != "0.0" ]]; then
    sleep "${wait_sec}"
  fi
}

require_relay_key() {
  if [[ -z "${RELAY_KEY}" ]]; then
    log "RELAY_KEY is empty. Authenticated endpoints will likely return 401."
  fi
}

curl_json() {
  local method="$1"
  local url="$2"
  local data="${3:-}"

  if [[ -n "${data}" ]]; then
    curl -sS -X "${method}" "${url}" \
      -H "${AUTH_HEADER}" \
      -H "${X_RELAY_HEADER}" \
      -H "Content-Type: application/json" \
      -d "${data}"
  else
    curl -sS -X "${method}" "${url}" \
      -H "${AUTH_HEADER}" \
      -H "${X_RELAY_HEADER}"
  fi
}

curl_stream() {
  local url="$1"
  local data="$2"
  curl -N "${url}" \
    -H "${AUTH_HEADER}" \
    -H "${X_RELAY_HEADER}" \
    -H "Content-Type: application/json" \
    -d "${data}"
}

run_step() {
  local name="$1"
  local method="$2"
  local url="$3"
  local data="${4:-}"
  log "STEP: ${name}"
  if [[ "${method}" == "STREAM" ]]; then
    curl_stream "${url}" "${data}"
  else
    curl_json "${method}" "${url}" "${data}"
  fi
  echo
  sleep_chain "${CHAIN_WAIT_SEC}"
}

skip_step() {
  local name="$1"
  log "SKIP: ${name} (missing required ID)"
  sleep_chain "${CHAIN_WAIT_SEC}"
}

require_relay_key

log "Starting chain wait route checks against ${BASE_URL}"

run_step "Health" "GET" "${BASE_URL}/health"
run_step "Health v1" "GET" "${BASE_URL}/v1/health"

run_step "List models" "GET" "${BASE_URL}/v1/models"

if [[ -n "${MODEL_ID:-}" ]]; then
  run_step "Retrieve model" "GET" "${BASE_URL}/v1/models/${MODEL_ID}"
else
  skip_step "Retrieve model"
fi

run_step "Create embedding" "POST" "${BASE_URL}/v1/embeddings" \
  "{\"model\":\"${EMBED_MODEL}\",\"input\":\"hello\"}"

run_step "List files" "GET" "${BASE_URL}/v1/files"

if [[ -n "${FILE_ID:-}" ]]; then
  run_step "Retrieve file" "GET" "${BASE_URL}/v1/files/${FILE_ID}"
  run_step "Delete file" "DELETE" "${BASE_URL}/v1/files/${FILE_ID}"
else
  skip_step "Retrieve file"
  skip_step "Delete file"
fi

run_step "List vector stores" "GET" "${BASE_URL}/v1/vector_stores"

if [[ -n "${VECTOR_STORE_ID:-}" ]]; then
  run_step "Retrieve vector store" "GET" "${BASE_URL}/v1/vector_stores/${VECTOR_STORE_ID}"
else
  skip_step "Retrieve vector store"
fi

run_step "Image generation (root)" "POST" "${BASE_URL}/v1/images" \
  "{\"prompt\":\"${IMAGE_PROMPT}\",\"size\":\"1024x1024\"}"
run_step "Image generations" "POST" "${BASE_URL}/v1/images/generations" \
  "{\"prompt\":\"${IMAGE_PROMPT}\",\"size\":\"1024x1024\"}"

run_step "Create video job" "POST" "${BASE_URL}/v1/videos" \
  "{\"prompt\":\"${VIDEO_PROMPT}\",\"model\":\"${VIDEO_MODEL}\"}"

if [[ -n "${VIDEO_JOB_ID:-}" ]]; then
  run_step "Get video job" "GET" "${BASE_URL}/v1/videos/jobs/${VIDEO_JOB_ID}"
  run_step "Get video content" "GET" "${BASE_URL}/v1/videos/jobs/${VIDEO_JOB_ID}/content"
else
  skip_step "Get video job"
  skip_step "Get video content"
fi

run_step "List conversations" "GET" "${BASE_URL}/v1/conversations"

if [[ -n "${CONVERSATION_ID:-}" ]]; then
  run_step "Retrieve conversation" "GET" "${BASE_URL}/v1/conversations/${CONVERSATION_ID}"
  run_step "List conversation messages" "GET" "${BASE_URL}/v1/conversations/${CONVERSATION_ID}/messages"
  run_step "Delete conversation" "DELETE" "${BASE_URL}/v1/conversations/${CONVERSATION_ID}"
else
  skip_step "Retrieve conversation"
  skip_step "List conversation messages"
  skip_step "Delete conversation"
fi

run_step "Create response" "POST" "${BASE_URL}/v1/responses" \
  "{\"model\":\"${MODEL}\",\"input\":\"ping\"}"

if [[ "${STREAM}" == "true" ]]; then
  run_step "Stream response" "STREAM" "${BASE_URL}/v1/responses:stream" \
    "{\"model\":\"${MODEL}\",\"input\":\"ping\",\"stream\":true}"
else
  log "SKIP: Stream response (STREAM=false)"
fi

if [[ -n "${RESPONSE_ID:-}" ]]; then
  run_step "Retrieve response" "GET" "${BASE_URL}/v1/responses/${RESPONSE_ID}"
  run_step "Cancel response" "POST" "${BASE_URL}/v1/responses/${RESPONSE_ID}/cancel"
else
  skip_step "Retrieve response"
  skip_step "Cancel response"
fi

run_step "Realtime sessions" "POST" "${BASE_URL}/v1/realtime/sessions" \
  "{\"model\":\"${MODEL}\"}"

run_step "List tools" "GET" "${BASE_URL}/v1/tools"

if [[ -n "${TOOL_ID:-}" ]]; then
  run_step "Retrieve tool" "GET" "${BASE_URL}/v1/tools/${TOOL_ID}"
else
  skip_step "Retrieve tool"
fi

run_step "Actions ping" "GET" "${BASE_URL}/actions/ping"
run_step "Actions ping v1" "GET" "${BASE_URL}/v1/actions/ping"
run_step "Actions relay info" "GET" "${BASE_URL}/actions/relay_info"
run_step "Actions relay info v1" "GET" "${BASE_URL}/v1/actions/relay_info"

if [[ -n "${UPLOAD_ID:-}" ]]; then
  run_step "Actions upload parts" "POST" "${BASE_URL}/v1/actions/uploads/${UPLOAD_ID}/parts" \
    "{\"part_number\":1,\"data_base64\":\"SGVsbG8=\"}"
  run_step "Actions upload complete" "POST" "${BASE_URL}/v1/actions/uploads/${UPLOAD_ID}/complete" \
    "{\"parts\":[{\"part_number\":1,\"etag\":\"etag\"}]}"
  run_step "Actions upload cancel" "POST" "${BASE_URL}/v1/actions/uploads/${UPLOAD_ID}/cancel"
else
  skip_step "Actions upload parts"
  skip_step "Actions upload complete"
  skip_step "Actions upload cancel"
fi

run_step "Actions videos" "POST" "${BASE_URL}/v1/actions/videos" \
  "{\"prompt\":\"${VIDEO_PROMPT}\",\"model\":\"${VIDEO_MODEL}\"}"

log "Completed chain wait route checks."
