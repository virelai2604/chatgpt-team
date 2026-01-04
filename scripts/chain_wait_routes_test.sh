#!/usr/bin/env bash
set -euo pipefail

# ---------------------------
# Output/Logging Hardening
# ---------------------------
LOG_FILE="${LOG_FILE:-run.log}"
exec 3>>"${LOG_FILE}"

timestamp() { date +"%Y-%m-%dT%H:%M:%S%z"; }

log() {
  local msg="[$(timestamp)] $*"
  printf "%s\n" "${msg}" >&3
  printf "%s\n" "${msg}" || true
}

emit() {
  # Grep-stable lines (no timestamp prefix)
  # Still mirrored to FD3 for auditability.
  local line="$*"
  printf "%s\n" "${line}" >&3
  printf "%s\n" "${line}" || true
}

blank() {
  printf "\n" >&3
  printf "\n" || true
}

trap '' PIPE

# ---------------------------
# Config
# ---------------------------
BASE_URL="${BASE_URL:-https://chatgpt-team-relay.onrender.com}"
CHAIN_WAIT_SEC="${CHAIN_WAIT_SEC:-0.5}"

POLL_INTERVAL_SEC="${POLL_INTERVAL_SEC:-2}"
POLL_TIMEOUT_SEC="${POLL_TIMEOUT_SEC:-180}"

CURL_CONNECT_TIMEOUT="${CURL_CONNECT_TIMEOUT:-10}"
CURL_MAX_TIME="${CURL_MAX_TIME:-30}"
CURL_HTTP1="${CURL_HTTP1:-false}"

RELAY_KEY="${RELAY_KEY:-}"
AUTH_HEADER="${AUTH_HEADER:-Authorization: Bearer ${RELAY_KEY}}"
X_RELAY_HEADER="X-Relay-Key: ${RELAY_KEY}"

# Limit body capture. Increase if you need full JSON for debugging.
MAX_BODY_BYTES="${MAX_BODY_BYTES:-200000}"

# Optional feature toggles
ENABLE_RESPONSES="${ENABLE_RESPONSES:-true}"          # /v1/responses
ENABLE_FILES_UPLOAD="${ENABLE_FILES_UPLOAD:-false}"  # /v1/files upload (multipart)
ENABLE_VIDEO="${ENABLE_VIDEO:-false}"                # /v1/videos jobs polling

# Models
EMBED_MODEL="${EMBED_MODEL:-text-embedding-3-small}"
TEXT_MODEL="${TEXT_MODEL:-gpt-4.1-mini}"

# ---------------------------
# State
# ---------------------------
LAST_STATUS=""
LAST_BODY_JSON=""
LAST_CURL_EXIT=""

# Chained IDs
MODEL_ID=""
FILE_ID=""
RESPONSE_ID=""
CONVERSATION_ID=""
VIDEO_JOB_ID=""

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

shorten() {
  local text="$1"
  local max_len="${2:-220}"
  if [[ ${#text} -le ${max_len} ]]; then echo "${text}"; else echo "${text:0:${max_len}}..."; fi
}

capture_body() {
  local tmp_body="$1"
  if [[ -f "${tmp_body}" ]]; then
    LAST_BODY_JSON="$(head -c "${MAX_BODY_BYTES}" "${tmp_body}")"
    rm -f "${tmp_body}"
  else
    LAST_BODY_JSON=""
  fi
}

curl_json() {
  local method="$1"
  local url="$2"
  local data="${3:-}"
  local tmp_body
  tmp_body="$(mktemp)"

  local -a args
  args=(-sS --connect-timeout "${CURL_CONNECT_TIMEOUT}" --max-time "${CURL_MAX_TIME}")
  if [[ "${CURL_HTTP1}" == "true" ]]; then
    args+=(--http1.1)
  fi

  log "REQ: ${method} ${url}"

  set +e
  if [[ -n "${data}" ]]; then
    LAST_STATUS="$(
      curl "${args[@]}" -X "${method}" "${url}" \
        -H "${AUTH_HEADER}" -H "${X_RELAY_HEADER}" -H "Content-Type: application/json" \
        -d "${data}" \
        -o "${tmp_body}" -w "%{http_code}"
    )"
    LAST_CURL_EXIT="$?"
  else
    LAST_STATUS="$(
      curl "${args[@]}" -X "${method}" "${url}" \
        -H "${AUTH_HEADER}" -H "${X_RELAY_HEADER}" \
        -o "${tmp_body}" -w "%{http_code}"
    )"
    LAST_CURL_EXIT="$?"
  fi
  set -e

  if [[ "${LAST_CURL_EXIT}" != "0" ]]; then
    LAST_STATUS="000"
  fi

  capture_body "${tmp_body}"
  log "RESP: status=${LAST_STATUS} curl_exit=${LAST_CURL_EXIT} body_len=${#LAST_BODY_JSON}"
}

# Multipart upload (optional)
curl_multipart() {
  local url="$1"
  local file_path="$2"
  local purpose="$3"
  local tmp_body
  tmp_body="$(mktemp)"

  local -a args
  args=(-sS --connect-timeout "${CURL_CONNECT_TIMEOUT}" --max-time "${CURL_MAX_TIME}")
  if [[ "${CURL_HTTP1}" == "true" ]]; then
    args+=(--http1.1)
  fi

  log "REQ: POST(multipart) ${url} file=${file_path} purpose=${purpose}"

  set +e
  LAST_STATUS="$(
    curl "${args[@]}" -X POST "${url}" \
      -H "${AUTH_HEADER}" -H "${X_RELAY_HEADER}" \
      -F "purpose=${purpose}" \
      -F "file=@${file_path}" \
      -o "${tmp_body}" -w "%{http_code}"
  )"
  LAST_CURL_EXIT="$?"
  set -e

  if [[ "${LAST_CURL_EXIT}" != "0" ]]; then
    LAST_STATUS="000"
  fi

  capture_body "${tmp_body}"
  log "RESP: status=${LAST_STATUS} curl_exit=${LAST_CURL_EXIT} body_len=${#LAST_BODY_JSON}"
}

is_2xx() { [[ "$1" =~ ^2 ]]; }

json_get() {
  # Minimal JSON path getter. Prints empty string on failure.
  local path="$1"
  python - <<'PY' "${path}" || true
import json, os, sys
path = sys.argv[1].split(".") if len(sys.argv) > 1 else []
raw = os.environ.get("LAST_BODY_JSON","")
if not raw.strip():
  print("")
  sys.exit(0)
try:
  obj = json.loads(raw)
except Exception:
  print("")
  sys.exit(0)

cur = obj
for seg in path:
  if not seg:
    continue
  if seg.isdigit():
    idx = int(seg)
    if isinstance(cur, list) and 0 <= idx < len(cur):
      cur = cur[idx]
    else:
      print("")
      sys.exit(0)
  else:
    if isinstance(cur, dict) and seg in cur:
      cur = cur[seg]
    else:
      print("")
      sys.exit(0)

if cur is None:
  print("")
elif isinstance(cur, (dict, list)):
  print(json.dumps(cur, ensure_ascii=False))
else:
  print(str(cur))
PY
}

extract_first_data_id() { json_get "data.0.id"; }
extract_id() { json_get "id"; }

record_pass() { PASS_COUNT=$((PASS_COUNT + 1)); log "PASS: $1 (${LAST_STATUS})"; }
record_fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); log "FAIL: $1 (${LAST_STATUS}) body=$(shorten "${LAST_BODY_JSON}")"; }
record_skip() { SKIP_COUNT=$((SKIP_COUNT + 1)); log "SKIP: $1"; }

wait_until_ready_status_field() {
  # Polls a URL until JSON field equals expected value.
  local name="$1" url="$2" field_path="$3" expected="$4"
  local start; start="$(date +%s)"

  while true; do
    curl_json "GET" "${url}"
    local val
    val="$(extract_env_and_get "${field_path}")"
    if [[ "${val}" == "${expected}" ]]; then
      emit "READY_${name}=true"
      log "READY: ${name} field ${field_path} == ${expected}"
      return 0
    fi

    local now elapsed
    now="$(date +%s)"; elapsed="$((now - start))"
    if (( elapsed >= POLL_TIMEOUT_SEC )); then
      emit "READY_${name}=false"
      log "TIMEOUT: ${name} waiting ${field_path}==${expected} last_val=${val}"
      return 1
    fi
    sleep "${POLL_INTERVAL_SEC}"
  done
}

extract_env_and_get() {
  # helper: uses LAST_BODY_JSON through env
  local p="$1"
  LAST_BODY_JSON="${LAST_BODY_JSON}" python - <<'PY' "${p}" || true
import json, os, sys
p = sys.argv[1].split(".")
raw = os.environ.get("LAST_BODY_JSON","")
try:
  obj = json.loads(raw) if raw.strip() else {}
except Exception:
  print("")
  raise SystemExit(0)
cur=obj
for seg in p:
  if seg.isdigit():
    i=int(seg)
    if isinstance(cur,list) and 0<=i<len(cur): cur=cur[i]
    else: print(""); raise SystemExit(0)
  else:
    if isinstance(cur,dict) and seg in cur: cur=cur[seg]
    else: print(""); raise SystemExit(0)
if cur is None: print("")
elif isinstance(cur,(dict,list)):
  print(json.dumps(cur, ensure_ascii=False))
else:
  print(str(cur))
PY
}

chain_from_models_list() {
  local mid; mid="$(extract_first_data_id)"
  if [[ -n "${mid}" ]]; then
    MODEL_ID="${mid}"
    emit "CHAIN_MODEL_ID=${MODEL_ID}"
  fi
}

chain_from_files_list() {
  local fid; fid="$(extract_first_data_id)"
  if [[ -n "${fid}" ]]; then
    FILE_ID="${fid}"
    emit "CHAIN_FILE_ID=${FILE_ID}"
  fi
}

chain_from_responses_create() {
  local rid; rid="$(extract_id)"
  if [[ -n "${rid}" ]]; then
    RESPONSE_ID="${rid}"
    emit "CHAIN_RESPONSE_ID=${RESPONSE_ID}"
  fi
  # optional conversation id if present
  local cid; cid="$(json_get "conversation.id")"
  if [[ -n "${cid}" ]]; then
    CONVERSATION_ID="${cid}"
    emit "CHAIN_CONVERSATION_ID=${CONVERSATION_ID}"
  fi
}

chain_from_video_create() {
  local vid; vid="$(extract_id)"
  if [[ -n "${vid}" ]]; then
    VIDEO_JOB_ID="${vid}"
    emit "CHAIN_VIDEO_JOB_ID=${VIDEO_JOB_ID}"
  fi
}

ground_truth_get() {
  # Emits GT_* lines: endpoint reachability using chained IDs.
  local name="$1" url="$2"
  curl_json "GET" "${url}"
  if is_2xx "${LAST_STATUS}"; then
    emit "GT_${name}=true"
  else
    emit "GT_${name}=false"
  fi
}

run_step_json() {
  local name="$1" method="$2" url="$3" data="${4:-}"

  log "STEP: ${name}"
  curl_json "${method}" "${url}" "${data}"

  if is_2xx "${LAST_STATUS}"; then
    record_pass "${name}"
  else
    record_fail "${name}"
  fi

  blank
  sleep "${CHAIN_WAIT_SEC}"
}

on_exit() {
  local ec="$?"
  log "SUMMARY: PASS=${PASS_COUNT} FAIL=${FAIL_COUNT} SKIP=${SKIP_COUNT}"
  log "EXIT: code=${ec}"
  exec 3>&-
  # If any FAIL occurred, exit 1.
  if [[ "${FAIL_COUNT}" -gt 0 ]]; then
    exit 1
  fi
  exit "${ec}"
}
trap on_exit EXIT

# ---------------------------
# Start
# ---------------------------
log "Starting chain wait route checks against ${BASE_URL}"
log "LOG_FILE=${LOG_FILE}"
log "CURL_CONNECT_TIMEOUT=${CURL_CONNECT_TIMEOUT} CURL_MAX_TIME=${CURL_MAX_TIME} CURL_HTTP1=${CURL_HTTP1}"
log "POLL_TIMEOUT_SEC=${POLL_TIMEOUT_SEC} POLL_INTERVAL_SEC=${POLL_INTERVAL_SEC}"
log "ENABLE_RESPONSES=${ENABLE_RESPONSES} ENABLE_FILES_UPLOAD=${ENABLE_FILES_UPLOAD} ENABLE_VIDEO=${ENABLE_VIDEO}"

# Core
run_step_json "Health" "GET" "${BASE_URL}/health"
run_step_json "Health v1" "GET" "${BASE_URL}/v1/health"
run_step_json "Manifest" "GET" "${BASE_URL}/v1/manifest"
run_step_json "OpenAPI actions" "GET" "${BASE_URL}/openapi.actions.json"
run_step_json "Actions ping" "GET" "${BASE_URL}/actions/ping"

# Models -> CHAIN_MODEL_ID + optional GT
run_step_json "List models" "GET" "${BASE_URL}/v1/models"
if is_2xx "${LAST_STATUS}"; then
  chain_from_models_list
  if [[ -n "${MODEL_ID}" ]]; then
    ground_truth_get "MODEL_ID" "${BASE_URL}/v1/models/${MODEL_ID}"
  fi
fi

# Embeddings
run_step_json "Embeddings" "POST" "${BASE_URL}/v1/embeddings" \
  "{\"model\":\"${EMBED_MODEL}\",\"input\":\"hello\"}"

# Files list -> CHAIN_FILE_ID + GT
run_step_json "List files" "GET" "${BASE_URL}/v1/files"
if is_2xx "${LAST_STATUS}"; then
  chain_from_files_list
  if [[ -n "${FILE_ID}" ]]; then
    ground_truth_get "FILE_ID" "${BASE_URL}/v1/files/${FILE_ID}"
  fi
fi

# Optional: upload a tiny file, then list+retrieve it
if [[ "${ENABLE_FILES_UPLOAD}" == "true" ]]; then
  tmp_up="$(mktemp)"
  printf "ping" > "${tmp_up}"
  log "STEP: Upload file"
  curl_multipart "${BASE_URL}/v1/files" "${tmp_up}" "batch"
  rm -f "${tmp_up}"

  if is_2xx "${LAST_STATUS}"; then
    local_up_id="$(extract_id)"
    if [[ -n "${local_up_id}" ]]; then
      FILE_ID="${local_up_id}"
      emit "CHAIN_FILE_ID=${FILE_ID}"
      ground_truth_get "FILE_ID" "${BASE_URL}/v1/files/${FILE_ID}"
    fi
    record_pass "Upload file"
  else
    record_fail "Upload file"
  fi
  blank
  sleep "${CHAIN_WAIT_SEC}"
else
  record_skip "Upload file"
fi

# Optional: Responses create -> CHAIN_RESPONSE_ID + GT
if [[ "${ENABLE_RESPONSES}" == "true" ]]; then
  run_step_json "Responses create" "POST" "${BASE_URL}/v1/responses" \
    "{\"model\":\"${TEXT_MODEL}\",\"input\":\"say ok\"}"
  if is_2xx "${LAST_STATUS}"; then
    chain_from_responses_create
    if [[ -n "${RESPONSE_ID}" ]]; then
      ground_truth_get "RESPONSE_ID" "${BASE_URL}/v1/responses/${RESPONSE_ID}"
    fi
  fi
else
  record_skip "Responses create"
fi

# Optional: video job flow (endpoint names vary; keep gated)
if [[ "${ENABLE_VIDEO}" == "true" ]]; then
  run_step_json "Videos create" "POST" "${BASE_URL}/v1/videos" \
    "{\"model\":\"sora-2\",\"prompt\":\"a cat running\"}"
  if is_2xx "${LAST_STATUS}"; then
    chain_from_video_create
    if [[ -n "${VIDEO_JOB_ID}" ]]; then
      # Ground truth: job exists
      ground_truth_get "VIDEO_JOB_ID" "${BASE_URL}/v1/videos/jobs/${VIDEO_JOB_ID}"
      # Wait until status == "succeeded" (adjust if your API differs)
      wait_until_ready_status_field "VIDEO_JOB_STATUS" \
        "${BASE_URL}/v1/videos/jobs/${VIDEO_JOB_ID}" "status" "succeeded" || true
      # If your relay supports content endpoint:
      ground_truth_get "VIDEO_JOB_CONTENT" "${BASE_URL}/v1/videos/jobs/${VIDEO_JOB_ID}/content"
    fi
  fi
else
  record_skip "Videos create"
fi

log "Completed full suite."
