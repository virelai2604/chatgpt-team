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
  # Prints "METHOD /path" (sorted, unique) from an OpenAPI JSON doc.
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

# Choose the proxy import path automatically if not set.
detect_proxy_import_path() {
  if [[ -n "${PROXY_IMPORT_PATH}" ]]; then
    echo "$PROXY_IMPORT_PATH"
    return
  fi

  # Try common locations used in this project.
  if python3 -c "import importlib; importlib.import_module('app.routes.proxy')" >/dev/null 2>&1; then
    echo "app.routes.proxy"
    return
  fi
  if python3 -c "import importlib; importlib.import_module('app.api.proxy')" >/dev/null 2>&1; then
    echo "app.api.proxy"
    return
  fi

  # Fallback: try a top-level proxy module.
  if python3 -c "import importlib; importlib.import_module('proxy')" >/dev/null 2>&1; then
    echo "proxy"
    return
  fi

  echo ""  # not found
}

PROXY_MOD="$(detect_proxy_import_path)"

# Ask the relay proxy module whether a method/path is allowlisted (and not blocked).
# Returns: "ALLOW" or "DENY:<reason>" or "NO_PROXY_MODULE"
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

# Optional helpers (implementation-dependent)
normalize = getattr(mod, "_normalize_path", None)
blocked_reason = getattr(mod, "_blocked_reason", None)
is_allowlisted = getattr(mod, "_is_allowlisted", None)

if normalize:
    try:
        path_n = normalize(path)
    except Exception as e:
        print(f"DENY:normalize_error:{type(e).__name__}")
        raise SystemExit(0)
else:
    path_n = path

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

# Heuristic buckets for UI compatibility, used when not Actions-direct and not proxy-harness.
heuristic_bucket() {
  local method="$1"
  local path="$2"

  # Legacy duplicates (prefer /v1/* in Actions)
  if [[ "$path" == "/health" || "$path" == "/actions/ping" || "$path" == "/actions/relay_info" ]]; then
    echo "EXCLUDE_LEGACY"
    return
  fi

  # Wildcard/catch-all routers - Actions should not expose
  if [[ "$path" == *"{path}"* || "$path" == *"{path:path}"* ]]; then
    echo "EXCLUDE_WILDCARD"
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

  # Multipart endpoints that Actions can't call directly (typical)
  if [[ "$method" == "POST" && "$path" == "/v1/files" ]]; then
    echo "WRAPPER_FILES_UPLOAD"
    return
  fi
  if [[ "$method" == "POST" && ( "$path" == "/v1/images/edits" || "$path" == "/v1/images/variations" ) ]]; then
    echo "WRAPPER_IMAGES_MULTIPART"
    return
  fi
  if [[ "$path" == /v1/uploads* ]]; then
    echo "WRAPPER_UPLOADS_RESUMABLE"
    return
  fi
  if [[ "$method" == "POST" && "$path" == "/v1/videos" ]]; then
    echo "WRAPPER_VIDEOS_MULTIPART"
    return
  fi

  # Default unknown if it didn't match any rule.
  echo "UNKNOWN"
}

main() {
  local full_url="${RELAY_BASE_URL%/}/openapi.json"
  local actions_url="${RELAY_BASE_URL%/}/openapi.actions.json"

  echo "RELAY_BASE_URL=${RELAY_BASE_URL}"
  echo "Full OpenAPI:    $full_url"
  echo "Actions OpenAPI: $actions_url"
  echo

  # Fetch and extract ops
  local full_ops actions_ops
  full_ops="$(fetch_json "$full_url" | extract_ops)"
  actions_ops="$(fetch_json "$actions_url" | extract_ops)"

  # Save to temp files for membership checks
  local tmpdir
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT

  printf "%s\n" "$full_ops" > "$tmpdir/full_ops.txt"
  printf "%s\n" "$actions_ops" > "$tmpdir/actions_ops.txt"

  echo "Counts:"
  echo "  full_ops:    $(wc -l < "$tmpdir/full_ops.txt")"
  echo "  actions_ops: $(wc -l < "$tmpdir/actions_ops.txt")"
  echo "  proxy_module: ${PROXY_MOD:-<not detected>}"
  echo

  # Buckets
  local out="$tmpdir/report.tsv"
  : > "$out"

  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local method path
    method="${line%% *}"
    path="${line#* }"

    local bucket detail

    if grep -Fxq "$line" "$tmpdir/actions_ops.txt" && [[ "$path" == /v1/* ]]; then
      bucket="ACTIONS_DIRECT"
      detail="in_openapi.actions.json"
    else
      local pd
      pd="$(proxy_decision "$method" "$path")"
      if [[ "$pd" == "ALLOW" ]]; then
        bucket="PROXY_HARNESS"
        detail="allowlisted_by_proxy"
      else
        bucket="$(heuristic_bucket "$method" "$path")"
        detail="$pd"
      fi
    fi

    printf "%s\t%s\t%s\t%s\n" "$bucket" "$method" "$path" "$detail" >> "$out"
  done < "$tmpdir/full_ops.txt"

  echo "Bucket summary:"
  cut -f1 "$out" | sort | uniq -c | sort -nr
  echo

  for b in ACTIONS_DIRECT PROXY_HARNESS WRAPPER_FILES_UPLOAD WRAPPER_UPLOADS_RESUMABLE WRAPPER_STREAM WRAPPER_IMAGES_MULTIPART WRAPPER_VIDEOS_MULTIPART EXCLUDE_BINARY EXCLUDE_WILDCARD EXCLUDE_LEGACY EXCLUDE_COLON_PATH UNKNOWN; do
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
    echo "These endpoints were not assigned to any bucket. Add heuristics or proxy allowlist/wrapper policy."
    exit 2
  fi

  echo "OK: All full endpoints mapped to a bucket (no UNKNOWN)."
}

main "$@"
