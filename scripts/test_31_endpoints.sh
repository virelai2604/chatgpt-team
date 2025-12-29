#!/usr/bin/env bash
set -euo pipefail

: "${RELAY_BASE_URL:=https://chatgpt-team-relay.onrender.com}"
: "${RELAY_KEY:?Set RELAY_KEY}"
: "${TIMEOUT:=25}"

: "${RESPONSES_MODEL:=gpt-4.1-mini}"
: "${EMBEDDINGS_MODEL:=text-embedding-3-small}"
: "${IMAGES_PROMPT:=smoke test image}"
: "${EMBEDDINGS_INPUT:=smoke test}"

: "${FILE_ID:=}"
: "${BATCH_ID:=}"
: "${VIDEO_ID:=}"
: "${VECTOR_STORE_PATH:=}"
: "${CONV_PATH:=}"

: "${RUN_DELETES:=0}"

say() { printf "%s\n" "$*"; }

curl_json() {
  local method="$1"; shift
  local url="$1"; shift
  local data="${1:-}"

  if [[ -n "${data}" ]]; then
    curl -sS --max-time "${TIMEOUT}" -X "${method}" "${url}" \
      -H "X-Relay-Key: ${RELAY_KEY}" \
      -H "Content-Type: application/json" \
      -d "${data}"
  else
    curl -sS --max-time "${TIMEOUT}" -X "${method}" "${url}" \
      -H "X-Relay-Key: ${RELAY_KEY}"
  fi
}

# Hard-fail only on relay-level blocks (proxy policy), not upstream OpenAI validation errors.
is_relay_block() {
  grep -qiE \
    'method/path not allowlisted for /v1/proxy|not_allowlisted|DENY:|blocked prefix|blocked suffix|paths are not allowed|upload_not_pending' \
    <<<"$1"
}

ok_or_warn() {
  local name="$1"
  local out="$2"

  if is_relay_block "$out"; then
    say "FAIL  $name  (relay blocked / not allowlisted)"
    echo "$out" | sed -n '1,120p'
    return 1
  fi

  if grep -qE '"type":\s*"invalid_request_error"|"type":\s*"authentication_error"|"error":' <<<"$out"; then
    say "OK    $name  (reachable; upstream error is acceptable for smoke)"
    return 0
  fi

  say "OK    $name"
  return 0
}

proxy_call() {
  local m="$1"; shift
  local p="$1"; shift
  local body="${1:-}"

  local payload
  if [[ -n "$body" ]]; then
    payload="$(jq -nc --arg method "$m" --arg path "$p" --argjson body "$body" '{method:$method,path:$path,body:$body}')"
  else
    payload="$(jq -nc --arg method "$m" --arg path "$p" '{method:$method,path:$path}')"
  fi

  curl_json "POST" "${RELAY_BASE_URL%/}/v1/proxy" "$payload"
}

should_skip_op() {
  local raw_path="$1"
  case "$raw_path" in
    *"{file_id}"*) [[ -z "$FILE_ID" ]] && return 0 ;;
    *"{batch_id}"*) [[ -z "$BATCH_ID" ]] && return 0 ;;
    *"{video_id}"*) [[ -z "$VIDEO_ID" ]] && return 0 ;;
    "/v1/vector_stores/{path}") [[ -z "$VECTOR_STORE_PATH" ]] && return 0 ;;
    "/v1/conversations/{path}"|"/v1/conversations/{path}"*) [[ -z "$CONV_PATH" ]] && return 0 ;;
  esac
  return 1
}

substitute_path_vars() {
  local p="$1"
  p="${p//\{file_id\}/$FILE_ID}"
  p="${p//\{batch_id\}/$BATCH_ID}"
  p="${p//\{video_id\}/$VIDEO_ID}"
  p="${p//\{path\}/$VECTOR_STORE_PATH}"
  if [[ "$p" == *"/v1/conversations/{path}"* ]]; then
    p="${p//\{path\}/$CONV_PATH}"
  fi
  echo "$p"
}

declare -a ACTIONS_DIRECT_OPS=(
  "GET  /health"
  "GET  /v1/health"
  "GET  /v1/models"
  "POST /v1/actions/images/edits"
  "POST /v1/actions/images/variations"
  "POST /v1/embeddings"
  "POST /v1/images/edits"
  "POST /v1/images/generations"
  "POST /v1/images/variations"
  "POST /v1/proxy"
  "POST /v1/realtime/sessions"
  "POST /v1/responses"
  "POST /v1/responses/compact"
)

declare -a PROXY_OPS=(
  "GET  /v1/containers"
  "GET  /v1/files"
  "GET  /v1/conversations"
  "GET  /v1/vector_stores"
  "GET  /v1/videos"
  "GET  /v1/batches"
  "POST /v1/batches"
  "GET  /v1/batches/{batch_id}"
  "POST /v1/batches/{batch_id}/cancel"
  "GET  /v1/files/{file_id}"
  "PUT  /v1/vector_stores"
  "PATCH /v1/vector_stores"
  "GET  /v1/videos/{video_id}"
  "GET  /v1/vector_stores/{path}"
  "POST /v1/vector_stores"
  "POST /v1/vector_stores/{path}"
  "GET  /v1/conversations/{path}"
  "POST /v1/conversations"
)

: "${FILES_UPLOAD_WRAPPER_PATH:=/v1/actions/files/upload}"

body_for_direct() {
  local method="$1" path="$2"
  case "$method $path" in
    "POST /v1/responses"|"POST /v1/responses/compact")
      jq -nc --arg model "$RESPONSES_MODEL" '{
        model:$model,
        input:[{role:"user",content:[{type:"input_text",text:"smoke test"}]}]
      }'
      ;;
    "POST /v1/embeddings")
      jq -nc --arg model "$EMBEDDINGS_MODEL" --arg input "$EMBEDDINGS_INPUT" '{
        model:$model,
        input:$input
      }'
      ;;
    "POST /v1/images/generations")
      jq -nc --arg prompt "$IMAGES_PROMPT" '{prompt:$prompt}'
      ;;
    "POST /v1/images/edits"|"POST /v1/images/variations"|"POST /v1/actions/images/edits"|"POST /v1/actions/images/variations")
      jq -nc '{note:"smoke test - expect upstream validation error"}'
      ;;
    "POST /v1/realtime/sessions")
      jq -nc --arg model "$RESPONSES_MODEL" '{model:$model}'
      ;;
    "POST /v1/proxy")
      jq -nc '{method:"GET",path:"/v1/models"}'
      ;;
    *)
      echo ""
      ;;
  esac
}

proxy_body_for() {
  local method="$1" path="$2"
  case "$method $path" in
    "POST /v1/batches")
      jq -nc '{note:"smoke test - expect upstream validation error unless full batch body provided"}'
      ;;
    "PUT /v1/vector_stores"|"PATCH /v1/vector_stores")
      jq -nc '{note:"smoke test - expect upstream validation error"}'
      ;;
    "POST /v1/vector_stores")
      jq -nc '{name:"smoke-test-vector-store"}'
      ;;
    "POST /v1/vector_stores/{path}")
      jq -nc '{note:"smoke test - expect upstream validation error unless path accepts this body"}'
      ;;
    "POST /v1/conversations")
      jq -nc '{note:"smoke test - expect upstream validation error if required fields missing"}'
      ;;
    *)
      echo ""
      ;;
  esac
}

say "RELAY_BASE_URL=${RELAY_BASE_URL}"
say "Testing 31 operations:"
say "  - 13 direct Actions ops"
say "  - 18 proxy ops"
say ""

fail=0

say "== DIRECT (Actions-native) =="
for spec in "${ACTIONS_DIRECT_OPS[@]}"; do
  method="$(awk '{print $1}' <<<"$spec")"
  path="$(awk '{print $2}' <<<"$spec")"
  url="${RELAY_BASE_URL%/}${path}"

  body="$(body_for_direct "$method" "$path")"
  out="$(curl_json "$method" "$url" "${body:-}")" || true

  if ! ok_or_warn "$method $path" "$out"; then
    fail=1
  fi
done

say ""
say "== PROXY (18 ops) =="
for spec in "${PROXY_OPS[@]}"; do
  method="$(awk '{print $1}' <<<"$spec")"
  raw_path="$(awk '{print $2}' <<<"$spec")"

  if should_skip_op "$raw_path"; then
    say "SKIP  $method $raw_path  (missing required ID env var)"
    continue
  fi

  path="$(substitute_path_vars "$raw_path")"
  body="$(proxy_body_for "$method" "$raw_path")"
  out="$(proxy_call "$method" "$path" "${body:-}")" || true

  if ! ok_or_warn "PROXY $method $raw_path" "$out"; then
    fail=1
  fi
done

say ""
say "== OPTIONAL: DELETE ops (opt-in) =="
if [[ "$RUN_DELETES" == "1" ]]; then
  say "RUN_DELETES=1 is set, but no deletes are configured in this suite by default."
else
  say "Deletes not executed. Set RUN_DELETES=1 and extend script if needed."
fi

say ""
say "== FILE UPLOAD WRAPPER (future) =="
say "Probing wrapper path: POST ${FILES_UPLOAD_WRAPPER_PATH}"
wrapper_url="${RELAY_BASE_URL%/}${FILES_UPLOAD_WRAPPER_PATH}"
out="$(curl_json "POST" "$wrapper_url" "$(jq -nc '{note:"smoke test wrapper - expected 404 until implemented"}')" || true)"
if grep -qE '"detail":\s*"Not Found"|404' <<<"$out"; then
  say "INFO  Wrapper not implemented yet (404). This is expected until you add it."
else
  ok_or_warn "POST ${FILES_UPLOAD_WRAPPER_PATH}" "$out" || fail=1
fi

say ""
if [[ "$fail" == "0" ]]; then
  say "PASS  31-op smoke test complete (reachable or acceptable upstream errors)."
else
  say "FAIL  One or more ops were blocked/not_allowlisted."
  exit 1
fi
