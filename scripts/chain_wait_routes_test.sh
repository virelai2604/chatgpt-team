#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Full Contract: Chain Wait Routes Test (stdout + pipe hardened)
# ============================================================
SCRIPT_VERSION="2026-01-04T22:25+0700-full-contract-fastfail-404"

# ---------------------------
# Output/Logging Hardening
# ---------------------------
LOG_FILE="${LOG_FILE:-run.log}"
exec 3>>"${LOG_FILE}"

# Mirror to stdout only if interactive TTY, unless explicitly forced.
STDOUT_MIRROR="${STDOUT_MIRROR:-auto}"
should_mirror_stdout() {
  case "${STDOUT_MIRROR}" in
    true) return 0 ;;
    false) return 1 ;;
    auto) [[ -t 1 ]] ;;
    *) [[ -t 1 ]] ;;
  esac
}

safe_print() {
  # Avoid broken pipe errors when stdout is closed by upstream tools.
  set +e
  printf "%s\n" "$1" || true
  set -e
}

safe_blank() {
  set +e
  printf "\n" || true
  set -e
}

timestamp() { date +"%Y-%m-%dT%H:%M:%S%z"; }

log() {
  local msg="[$(timestamp)] $*"
  printf "%s\n" "${msg}" >&3
  if should_mirror_stdout; then
    safe_print "${msg}"
  fi
}

emit() {
  # grep-stable lines: no timestamp prefix
  local line="$*"
  printf "%s\n" "${line}" >&3
  if should_mirror_stdout; then
    safe_print "${line}"
  fi
}

blank() {
  printf "\n" >&3
  if should_mirror_stdout; then
    safe_blank
  fi
}

# Ignore SIGPIPE globally (defensive)
trap '' PIPE

# ---------------------------
# Config
# ---------------------------
BASE_URL="${BASE_URL:-https://chatgpt-team-relay.onrender.com}"
CHAIN_WAIT_SEC="${CHAIN_WAIT_SEC:-0.5}"

POLL_INTERVAL_SEC="${POLL_INTERVAL_SEC:-2}"
POLL_TIMEOUT_SEC="${POLL_TIMEOUT_SEC:-180}"

# After successful create, allow a brief grace window for eventual consistency.
# If we see 404 this many consecutive times, treat as terminal (fast fail).
POLL_404_GRACE="${POLL_404_GRACE:-4}"

CURL_CONNECT_TIMEOUT="${CURL_CONNECT_TIMEOUT:-10}"
CURL_MAX_TIME="${CURL_MAX_TIME:-30}"
CURL_HTTP1="${CURL_HTTP1:-false}"

RELAY_KEY="${RELAY_KEY:-}"
AUTH_HEADER="Authorization: Bearer ${RELAY_KEY}"
X_RELAY_HEADER="X-Relay-Key: ${RELAY_KEY}"

MAX_BODY_BYTES="${MAX_BODY_BYTES:-200000}"

ENABLE_RESPONSES="${ENABLE_RESPONSES:-true}"
ENABLE_FILES_UPLOAD="${ENABLE_FILES_UPLOAD:-false}"
ENABLE_VIDEO="${ENABLE_VIDEO:-false}"

EMBED_MODEL="${EMBED_MODEL:-text-embedding-3-small}"
TEXT_MODEL="${TEXT_MODEL:-gpt-4.1-mini}"
REALTIME_MODEL="${REALTIME_MODEL:-gpt-4.1-mini}"
IMAGE_PROMPT="${IMAGE_PROMPT:-a small robot}"
VIDEO_PROMPT="${VIDEO_PROMPT:-a cat running}"
VIDEO_MODEL="${VIDEO_MODEL:-sora-2}"
UPLOAD_PURPOSE="${UPLOAD_PURPOSE:-assistants}"

PNG_1X1_B64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="

# ---------------------------
# State
# ---------------------------
LAST_STATUS=""
LAST_BODY_JSON=""
LAST_CURL_EXIT=""

MODEL_ID=""
FILE_ID=""
RESPONSE_ID=""
CONVERSATION_ID=""
VIDEO_JOB_ID=""
UPLOAD_ID=""
PART_ID=""

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

shorten() {
  local text="$1"
  local max_len="${2:-220}"
  if [[ ${#text} -le ${max_len} ]]; then
    echo "${text}"
  else
    echo "${text:0:${max_len}}..."
  fi
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
is_non_5xx() { [[ "$1" =~ ^[0-4][0-9][0-9]$ ]]; }

# ---------------------------
# JSON extraction (PIPE SAFE)
# ---------------------------
json_get() {
  local path="$1"
  if [[ -z "${LAST_BODY_JSON}" ]]; then
    printf "\n"
    return 0
  fi

  python -c '
import json, sys
path = sys.argv[1].split(".") if len(sys.argv) > 1 else []
raw = sys.stdin.read()
if not raw.strip():
  print("")
  raise SystemExit(0)
try:
  obj = json.loads(raw)
except Exception:
  print("")
  raise SystemExit(0)
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
      raise SystemExit(0)
  else:
    if isinstance(cur, dict) and seg in cur:
      cur = cur[seg]
    else:
      print("")
      raise SystemExit(0)
if cur is None:
  print("")
elif isinstance(cur, (dict, list)):
  print(json.dumps(cur, ensure_ascii=False))
else:
  print(str(cur))
' "$path" <<<"${LAST_BODY_JSON}" 2>/dev/null || true
}

extract_first_data_id() { json_get "data.0.id"; }
extract_id() { json_get "id"; }

record_pass() { PASS_COUNT=$((PASS_COUNT + 1)); log "PASS: $1 (${LAST_STATUS})"; }
record_fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); log "FAIL: $1 (${LAST_STATUS}) body=$(shorten "${LAST_BODY_JSON}")"; }
record_skip() { SKIP_COUNT=$((SKIP_COUNT + 1)); log "SKIP: $1"; }

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
  local cid; cid="$(json_get "conversation.id")"
  if [[ -n "${cid}" ]]; then
    CONVERSATION_ID="${cid}"
    emit "CHAIN_CONVERSATION_ID=${CONVERSATION_ID}"
  fi
}

chain_from_video_create() {
  local vid; vid="$(json_get "id")"
  if [[ -n "${vid}" ]]; then
    VIDEO_JOB_ID="${vid}"
    emit "CHAIN_VIDEO_JOB_ID=${VIDEO_JOB_ID}"
  fi
}

chain_from_upload_create() {
  local uid; uid="$(json_get "id")"
  if [[ -n "${uid}" ]]; then
    UPLOAD_ID="${uid}"
    emit "CHAIN_UPLOAD_ID=${UPLOAD_ID}"
  fi
}

chain_from_upload_part() {
  local pid; pid="$(json_get "id")"
  if [[ -n "${pid}" ]]; then
    PART_ID="${pid}"
    emit "CHAIN_PART_ID=${PART_ID}"
  fi
}

ground_truth_get() {
  local name="$1" url="$2"
  curl_json "GET" "${url}"

  if is_2xx "${LAST_STATUS}"; then
    emit "GT_${name}=true"
    return 0
  fi

  emit "GT_${name}=false"
  return 1
}

# Poll for 2xx with terminal-fast-fail behavior.
# - 404: allow small grace (POLL_404_GRACE) then fail (prevents spam and long hangs)
# - Other 4xx (except 429): fail immediately
# - 429: keep waiting (rate limit / transient)
poll_until_2xx() {
  local name="$1" url="$2"
  local deadline=$((SECONDS + POLL_TIMEOUT_SEC))
  local c404=0

  while (( SECONDS < deadline )); do
    curl_json "GET" "${url}"

    if is_2xx "${LAST_STATUS}"; then
      record_pass "${name}"
      return 0
    fi

    if [[ "${LAST_STATUS}" == "404" ]]; then
      c404=$((c404 + 1))
      if (( c404 >= POLL_404_GRACE )); then
        log "POLL: terminal 404 after ${c404} attempts (fast fail)"
        record_fail "${name}"
        return 1
      fi
    elif [[ "${LAST_STATUS}" =~ ^4 ]] && [[ "${LAST_STATUS}" != "429" ]]; then
      log "POLL: terminal ${LAST_STATUS} (fast fail)"
      record_fail "${name}"
      return 1
    fi

    sleep "${POLL_INTERVAL_SEC}"
  done

  record_fail "${name}"
  return 1
}

run_step_json() {
  local name="$1" method="$2" url="$3" data="${4:-}" expect_non_5xx="${5:-false}"

  log "STEP: ${name}"
  curl_json "${method}" "${url}" "${data}"

  if [[ "${expect_non_5xx}" == "true" ]]; then
    if is_non_5xx "${LAST_STATUS}"; then
      record_pass "${name}"
    else
      record_fail "${name}"
    fi
  else
    if is_2xx "${LAST_STATUS}"; then
      record_pass "${name}"
    else
      record_fail "${name}"
    fi
  fi

  blank
  sleep "${CHAIN_WAIT_SEC}"
}

on_exit() {
  local ec="$?"
  log "SUMMARY: PASS=${PASS_COUNT} FAIL=${FAIL_COUNT} SKIP=${SKIP_COUNT}"
  log "EXIT: code=${ec}"
  exec 3>&-
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
log "SCRIPT_VERSION=${SCRIPT_VERSION}"
log "LOG_FILE=${LOG_FILE}"
log "STDOUT_MIRROR=${STDOUT_MIRROR}"
log "CURL_CONNECT_TIMEOUT=${CURL_CONNECT_TIMEOUT} CURL_MAX_TIME=${CURL_MAX_TIME} CURL_HTTP1=${CURL_HTTP1}"
log "POLL_TIMEOUT_SEC=${POLL_TIMEOUT_SEC} POLL_INTERVAL_SEC=${POLL_INTERVAL_SEC} POLL_404_GRACE=${POLL_404_GRACE}"
log "ENABLE_RESPONSES=${ENABLE_RESPONSES} ENABLE_FILES_UPLOAD=${ENABLE_FILES_UPLOAD} ENABLE_VIDEO=${ENABLE_VIDEO}"

# 1) Health + discovery
run_step_json "Health" "GET" "${BASE_URL}/health"
run_step_json "Health v1" "GET" "${BASE_URL}/v1/health"
run_step_json "Manifest" "GET" "${BASE_URL}/v1/manifest"
run_step_json "OpenAPI actions" "GET" "${BASE_URL}/openapi.actions.json"
run_step_json "Actions ping" "GET" "${BASE_URL}/actions/ping"

# 2) Models + chain retrieve
run_step_json "List models" "GET" "${BASE_URL}/v1/models"
if is_2xx "${LAST_STATUS}"; then
  chain_from_models_list
  if [[ -n "${MODEL_ID}" ]]; then
    ground_truth_get "MODEL_ID" "${BASE_URL}/v1/models/${MODEL_ID}" || true
  fi
fi

# 3) Embeddings
run_step_json "Embeddings" "POST" "${BASE_URL}/v1/embeddings" \
  "{\"model\":\"${EMBED_MODEL}\",\"input\":\"hello\"}"

# 4) Files list + chain retrieve (use limit=1 to reduce truncation risk)
run_step_json "List files" "GET" "${BASE_URL}/v1/files?limit=1"
if is_2xx "${LAST_STATUS}"; then
  chain_from_files_list
  if [[ -n "${FILE_ID}" ]]; then
    ground_truth_get "FILE_ID" "${BASE_URL}/v1/files/${FILE_ID}" || true
  fi
fi

# 5) Optional upload file (multipart)
if [[ "${ENABLE_FILES_UPLOAD}" == "true" ]]; then
  tmp_up="$(mktemp)"
  printf "ping" > "${tmp_up}"
  log "STEP: Upload file"
  curl_multipart "${BASE_URL}/v1/files" "${tmp_up}" "batch"
  rm -f "${tmp_up}"

  if is_2xx "${LAST_STATUS}"; then
    FILE_ID="$(extract_id)"
    if [[ -n "${FILE_ID}" ]]; then
      emit "CHAIN_FILE_ID=${FILE_ID}"
      ground_truth_get "FILE_ID" "${BASE_URL}/v1/files/${FILE_ID}" || true
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

# 6) Images: generations + negative tests (non-5xx expected)
run_step_json "Image generations" "POST" "${BASE_URL}/v1/images/generations" \
  "{\"prompt\":\"${IMAGE_PROMPT}\",\"size\":\"1024x1024\"}"

run_step_json "Image variations" "POST" "${BASE_URL}/v1/images/variations" \
  "{\"image_base64\":\"${PNG_1X1_B64}\",\"model\":\"__invalid_model__\",\"n\":1,\"size\":\"256x256\"}" \
  true

run_step_json "Image edits" "POST" "${BASE_URL}/v1/images/edits" \
  "{\"image_base64\":\"${PNG_1X1_B64}\",\"mask_base64\":\"${PNG_1X1_B64}\",\"prompt\":\"edit\",\"model\":\"__invalid_model__\"}" \
  true

# 7) Actions images: negative tests (non-5xx expected)
run_step_json "Actions image variations" "POST" "${BASE_URL}/v1/actions/images/variations" \
  "{\"image_base64\":\"${PNG_1X1_B64}\",\"model\":\"__invalid_model__\",\"n\":1,\"size\":\"256x256\"}" \
  true

run_step_json "Actions image edits" "POST" "${BASE_URL}/v1/actions/images/edits" \
  "{\"image_base64\":\"${PNG_1X1_B64}\",\"mask_base64\":\"${PNG_1X1_B64}\",\"prompt\":\"edit\",\"model\":\"__invalid_model__\"}" \
  true

# 8) Vector stores + conversations (non-5xx expected)
run_step_json "List vector stores" "GET" "${BASE_URL}/v1/vector_stores?limit=1" "" true
run_step_json "List conversations" "GET" "${BASE_URL}/v1/conversations?limit=1" "" true

# 9) Responses create + poll retrieve (if enabled)
if [[ "${ENABLE_RESPONSES}" == "true" ]]; then
  run_step_json "Responses create" "POST" "${BASE_URL}/v1/responses" \
    '{"model":"'"${TEXT_MODEL}"'","input":"say ok"}'
  if is_2xx "${LAST_STATUS}"; then
    chain_from_responses_create
    if [[ -n "${RESPONSE_ID}" ]]; then
      poll_until_2xx "Response retrieve" "${BASE_URL}/v1/responses/${RESPONSE_ID}" || true
    fi
  fi
  run_step_json "Responses create (tools)" "POST" "${BASE_URL}/v1/responses" \
    '{"model":"'"${TEXT_MODEL}"'","input":"say ok","tool_choice":"none","tools":[{"type":"function","function":{"name":"noop","description":"No-op tool","parameters":{"type":"object","properties":{}}}}]}'
else
  record_skip "Responses create"
fi

# 10) Realtime sessions (non-5xx expected)
run_step_json "Realtime sessions" "POST" "${BASE_URL}/v1/realtime/sessions" \
  '{"model":"'"${REALTIME_MODEL}"'"}' true

# 11) Actions videos (non-5xx expected)
if [[ "${ENABLE_VIDEO}" == "true" ]]; then
  run_step_json "Actions video generations" "POST" "${BASE_URL}/v1/actions/videos/generations" \
    '{"prompt":"'"${VIDEO_PROMPT}"'","model":"__invalid_model__","size":"720x1280","seconds":4}' \
    true
else
  record_skip "Actions video generations"
fi

# 12) Actions upload flow (non-5xx expected)
run_step_json "Actions upload create" "POST" "${BASE_URL}/v1/actions/uploads" \
  '{"purpose":"'"${UPLOAD_PURPOSE}"'","filename":"test.txt","bytes":5,"mime_type":"text/plain"}' \
  true
if is_non_5xx "${LAST_STATUS}"; then
  chain_from_upload_create
fi

if [[ -n "${UPLOAD_ID}" ]]; then
  run_step_json "Actions upload parts" "POST" "${BASE_URL}/v1/actions/uploads/${UPLOAD_ID}/parts" \
    '{"filename":"test.txt","mime_type":"text/plain","data_base64":"SGVsbG8="}' \
    true
  if is_non_5xx "${LAST_STATUS}"; then
    chain_from_upload_part
  fi

  if [[ -n "${PART_ID}" ]]; then
    run_step_json "Actions upload complete" "POST" "${BASE_URL}/v1/actions/uploads/${UPLOAD_ID}/complete" \
      '{"part_ids":["'"${PART_ID}"'"]}' \
      true
  else
    record_skip "Actions upload complete"
  fi
else
  record_skip "Actions upload parts"
  record_skip "Actions upload complete"
fi
