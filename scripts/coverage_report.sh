#!/usr/bin/env bash
set -euo pipefail

: "${RELAY_BASE_URL:=https://chatgpt-team-relay.onrender.com}"
: "${TIMEOUT:=20}"

# If your relay requires auth for openapi endpoints, set RELAY_KEY.
RELAY_KEY="${RELAY_KEY:-}"

# Proxy module import path (override if your project uses a different module path).
# Examples:
#   export PROXY_IMPORT_PATH="app.routes.proxy"
#   export PROXY_IMPORT_PATH="app.api.proxy"
PROXY_IMPORT_PATH="${PROXY_IMPORT_PATH:-}"

hdrs=()
if [[ -n "${RELAY_KEY}" ]]; then
  hdrs+=( -H "X-Relay-Key: ${RELAY_KEY}" )
fi

fetch_json() {
  local url="$1"
  curl -sS --max-time "$TIMEOUT" "${hdrs[@]}" "$url"
}

extract_ops() {
  jq -r '
    .paths
    | to_entries[]
    | .key as $path
    | .value
    | to_entries[]
    | select(.key|IN("get","post","put","patch","delete","head","options"))
    | "\(.key|ascii_upcase) \($path)"
  ' | sort -u
}

detect_proxy_import_path() {
  if [[ -n "${PROXY_IMPORT_PATH}" ]]; then
    echo "$PROXY_IMPORT_PATH"
    return
  fi
  if python3 -c "import importlib; importlib.import_module('app.routes.proxy')" >/dev/null 2>&1; then
    echo "app.routes.proxy"
    return
  fi
  if python3 -c "import importlib; importlib.import_module('app.api.proxy')" >/dev/null 2>&1; then
    echo "app.api.proxy"
    return
  fi
  if python3 -c "import importlib; importlib.import_module('proxy')" >/dev/null 2>&1; then
    echo "proxy"
    return
  fi
  echo ""
}

PROXY_MOD="$(detect_proxy_import_path)"

# Instantiate OpenAPI template parameters (e.g., /v1/files/{file_id}) into representative concrete values
# so proxy allowlist regex checks reflect runtime behavior.
instantiate_openapi_path() {
  local p="$1"

  # Most common OpenAI-style IDs in your proxy allowlist
  p="$(echo "$p" | sed -E \
    -e 's/\{file_id\}/file-EXAMPLE123/g' \
    -e 's/\{batch_id\}/batch_EXAMPLE123/g' \
    -e 's/\{video_id\}/video-EXAMPLE123/g' \
    -e 's/\{image_id\}/image-EXAMPLE123/g' \
    -e 's/\{vector_store_id\}/vs_EXAMPLE123/g' \
    -e 's/\{assistant_id\}/asst_EXAMPLE123/g' \
    -e 's/\{thread_id\}/thread_EXAMPLE123/g' \
    -e 's/\{message_id\}/msg_EXAMPLE123/g' \
    -e 's/\{run_id\}/run_EXAMPLE123/g' \
    -e 's/\{upload_id\}/upload_EXAMPLE123/g' \
    -e 's/\{chunk_id\}/chunk_EXAMPLE123/g' \
  )"

  # Generic safe fallback: replace any remaining {param} with a token that contains no slashes.
  # This prevents template-literal mismatches while still letting allowlist enforcement do real work.
  p="$(echo "$p" | sed -E 's/\{[^\/}]+\}/EXAMPLE123/g')"

  echo "$p"
}

proxy_decision() {
  local method="$1"
  local path="$2"

  if [[ -z "$PROXY_MOD" ]]; then
    echo "NO_PROXY_MODULE"
    return
  fi

  python3 - <<PY
import importlib
mod = importlib.import_module("${PROXY_MOD}")
method = "${method}".strip().upper()
path = "${path}".strip()

normalize = getattr(mod, "_normalize_path", None)
blocked_reason = getattr(mod, "_blocked_reason", None)
is_allowlisted = getattr(mod, "_is_allowlisted", None)

path_n = path
if normalize:
    try:
        path_n = normalize(path)
    except Exception as e:
        print(f"DENY:normalize_error:{type(e).__name__}")
        raise SystemExit(0)

reason = None
if blocked_reason:
    try:
        reason = blocked_reason(method, path_n, {})
    except Exception as e:
        print(f"DENY:blocked_reason_error:{type(e).__name__}")
        raise SystemExit(0)

if reason:
    print(f"DENY:{reason}")
    raise SystemExit(0)

if is_allowlisted and is_allowlisted(method, path_n):
    print("ALLOW")
else:
    print("DENY:not_allowlisted")
PY
}

heuristic_bucket() {
  local method="$1"
  local path="$2"
  local proxy_detail="$3"

  # Legacy duplicates (prefer /v1/* in Actions)
  if [[ "$path" == "/health" || "$path" == "/actions/ping" || "$path" == "/actions/relay_info" ]]; then
    echo "EXCLUDE_LEGACY"
    return
  fi

  # Actions wrappers (explicit)
  if [[ "$path" == /v1/actions/uploads* || "$path" == "/v1/actions/videos" ]]; then
    echo "ACTIONS_DIRECT"
    return
  fi

  # Keep /v1/actions/* out of Actions by default unless explicitly exposed
  if [[ "$path" == "/v1/actions/ping" || "$path" == "/v1/actions/relay_info" ]]; then
    echo "EXCLUDE_META_V1"
    return
  fi

  # Wildcard/catch-all routers - Actions should not expose
  if [[ "$path" == *"{path}"* || "$path" == *"{path:path}"* ]]; then
    echo "EXCLUDE_WILDCARD"
    return
  fi

  # Conversations collection is broad; keep out unless intentionally allowlisted
  if [[ "$path" == "/v1/conversations" ]]; then
    echo "PROXY_CANDIDATE_CONVERSATIONS"
    return
  fi

  # Colon path: streaming variant
  if [[ "$path" == *":"* ]]; then
    if [[ "$path" == "/v1/responses:stream" ]]; then
      echo "WRAPPER_STREAM"
    else
      echo "EXCLUDE_COLON_PATH"
    fi
    return
  fi

  # Binary-ish content endpoints
  if [[ "$path" == */content || "$path" == *"/content" ]]; then
    echo "EXCLUDE_BINARY"
    return
  fi

  # Multipart endpoints that Actions can't call directly
  if [[ "$method" == "POST" && "$path" == "/v1/files" ]]; then
    echo "WRAPPER_FILES_UPLOAD"
    return
  fi

  if [[ "$path" == /v1/uploads* ]]; then
    echo "WRAPPER_UPLOADS_RESUMABLE"
    return
  fi

  # Local-only realtime helpers (explicitly excluded from proxy/actions)
  if [[ "$path" == "/v1/realtime/sessions/validate" || "$path" == "/v1/realtime/sessions/introspect" ]]; then
    echo "EXCLUDE_REALTIME_LOCAL"
    return
  fi

  if [[ "$method" == "POST" && ( "$path" == "/v1/images/edits" || "$path" == "/v1/images/variations" ) ]]; then
    echo "WRAPPER_IMAGES_MULTIPART"
    return
  fi

  if [[ "$method" == "POST" && ( "$path" == "/v1/videos" || "$path" == "/v1/videos/generations" || "$path" == "/v1/videos/{video_id}/remix" ) ]]; then
    echo "WRAPPER_VIDEOS_MULTIPART"
    return
  fi

  # Proxy candidates (JSON surfaces likely safe to proxy, but not allowlisted today)
  if [[ "$path" == "/v1/batches" || "$path" == "/v1/batches/{batch_id}" || "$path" == "/v1/batches/{batch_id}/cancel" ]]; then
    echo "PROXY_CANDIDATE_BATCHES"
    return
  fi

  if [[ "$path" == "/v1/files" || "$path" == "/v1/files/{file_id}" ]]; then
    echo "PROXY_CANDIDATE_FILES_META"
    return
  fi

  if [[ "$method" == "DELETE" && "$path" == "/v1/files/{file_id}" ]]; then
    echo "PROXY_CANDIDATE_FILES_DELETE"
    return
  fi

  if [[ "$path" == "/v1/vector_stores" && ( "$method" == "PUT" || "$method" == "PATCH" || "$method" == "DELETE" ) ]]; then
    echo "PROXY_CANDIDATE_VECTOR_STORES_ROOT_WRITE"
    return
  fi

  if [[ "$path" == "/v1/videos/generations" || "$path" == "/v1/videos/{video_id}/remix" ]]; then
    echo "PROXY_CANDIDATE_VIDEOS"
    return
  fi

  if [[ "$proxy_detail" == "DENY:not_allowlisted" ]]; then
    echo "UNKNOWN"
    return
  fi

  echo "UNKNOWN"
}

# Global cleanup var (trap-safe even with `set -u`)
TMPDIR_CLEANUP=""

cleanup() {
  if [[ -n "${TMPDIR_CLEANUP}" && -d "${TMPDIR_CLEANUP}" ]]; then
    rm -rf "${TMPDIR_CLEANUP}"
  fi
}
trap cleanup EXIT

main() {
  local full_url="${RELAY_BASE_URL%/}/openapi.json"
  local actions_url="${RELAY_BASE_URL%/}/openapi.actions.json"

  echo "RELAY_BASE_URL=${RELAY_BASE_URL}"
  echo "Full OpenAPI:    $full_url"
  echo "Actions OpenAPI: $actions_url"
  echo

  local full_ops actions_ops
  full_ops="$(fetch_json "$full_url" | extract_ops)"
  actions_ops="$(fetch_json "$actions_url" | extract_ops)"

  TMPDIR_CLEANUP="$(mktemp -d)"

  printf "%s\n" "$full_ops" > "$TMPDIR_CLEANUP/full_ops.txt"
  printf "%s\n" "$actions_ops" > "$TMPDIR_CLEANUP/actions_ops.txt"

  echo "Counts:"
  echo "  full_ops:    $(wc -l < "$TMPDIR_CLEANUP/full_ops.txt")"
  echo "  actions_ops: $(wc -l < "$TMPDIR_CLEANUP/actions_ops.txt")"
  echo "  proxy_module: ${PROXY_MOD:-<not detected>}"
  echo

  local out="$TMPDIR_CLEANUP/report.tsv"
  : > "$out"

  while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    # Parse: "METHOD /path"
    local method path
    method="${line%% *}"
    path="${line#* }"

    local bucket detail pd path_for_proxy
    if grep -Fxq "$line" "$TMPDIR_CLEANUP/actions_ops.txt" && [[ "$path" == /v1/* ]]; then
      bucket="ACTIONS_DIRECT"
      detail="in_openapi.actions.json"
    else
      # Instantiate template params before proxy allowlist evaluation (keeps report aligned with runtime).
      path_for_proxy="$(instantiate_openapi_path "$path")"
      pd="$(proxy_decision "$method" "$path_for_proxy")"
      if [[ "$pd" == "ALLOW" ]]; then
        bucket="PROXY_HARNESS"
        detail="allowlisted_by_proxy"
      else
        bucket="$(heuristic_bucket "$method" "$path" "$pd")"
        detail="$pd"
      fi
    fi

    printf "%s\t%s\t%s\t%s\n" "$bucket" "$method" "$path" "$detail" >> "$out"
  done < "$TMPDIR_CLEANUP/full_ops.txt"

  echo "Bucket summary:"
  cut -f1 "$out" | sort | uniq -c | sort -nr
  echo

  for b in ACTIONS_DIRECT PROXY_HARNESS \
           PROXY_CANDIDATE_BATCHES PROXY_CANDIDATE_FILES_META PROXY_CANDIDATE_FILES_DELETE \
           PROXY_CANDIDATE_VECTOR_STORES_ROOT_WRITE PROXY_CANDIDATE_CONVERSATIONS PROXY_CANDIDATE_VIDEOS \
           WRAPPER_FILES_UPLOAD WRAPPER_UPLOADS_RESUMABLE WRAPPER_STREAM WRAPPER_IMAGES_MULTIPART WRAPPER_VIDEOS_MULTIPART \
           EXCLUDE_BINARY EXCLUDE_WILDCARD EXCLUDE_LEGACY EXCLUDE_META_V1 EXCLUDE_COLON_PATH UNKNOWN; do
    local n
    n="$(awk -F'\t' -v B="$b" '$1==B{c++} END{print c+0}' "$out")"
    [[ "$n" -eq 0 ]] && continue
    echo "== $b ($n) =="
    awk -F'\t' -v B="$b" '$1==B{printf "%-6s %-55s  %s\n", $2, $3, $4}' "$out"
    echo
  done

  local unknown_count
  unknown_count="$(awk -F'\t' '$1=="UNKNOWN"{c++} END{print c+0}' "$out")"
  if [[ "$unknown_count" -gt 0 ]]; then
    echo "ERROR: UNKNOWN endpoints detected ($unknown_count)."
    echo "Guardrail: assign each new full endpoint to a bucket via proxy allowlist, wrapper policy, or explicit exclusion."
    exit 2
  fi

  echo "OK: All full endpoints mapped to a bucket (no UNKNOWN)."
  echo
  echo "Next actions:"
  echo "  - Review PROXY_CANDIDATE_* buckets and decide which to add to proxy allowlist."
  echo "  - Implement WRAPPER_* buckets if you need Actions coverage (multipart/uploads/streaming)."
}

main "$@"
