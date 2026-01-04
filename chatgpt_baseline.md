# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 3896cd6f44a7da6c58071c889574a3d5723c4363
Dirs: app tests static schemas src scripts/src
Root files: project-tree.md pyproject.toml chatgpt_sync.sh AGENTS.md __init__.py generate_tree.py
Mode: baseline
Generated: 2026-01-04T18:27:43+07:00

## TREE (repo root at 3896cd6f44a7da6c58071c889574a3d5723c4363)
```
 - .env.example.env
 - .gitattributes
 - .github
 - .gitignore
 - .gitleaks.toml
 - AGENTS.md
 - CONTRIBUTING.md
 - ChatGPT-API_reference_ground_truth-2025-10-29.pdf
 - Governence.md
 - P4_Cross_Domain_Analogy_Hybrid_Developer_v2_3_3.json
 - README.md
 - RELAY_CHECKLIST_v19.md
 - RELAY_PROGRESS_SUMMARY_v14.md
 - __init__.py
 - app
 - chatgpt_baseline.md
 - chatgpt_changes.md
 - chatgpt_sync.sh
 - data
 - docs
 - generate_tree.py
 - openai_models_2025-11.csv
 - path
 - project-tree.md
 - pyproject.toml
 - pytest.ini
 - render.yaml
 - requirements.txt
 - schemas
 - scripts
 - static
 - tests
```

## TREE (app/ at 3896cd6f44a7da6c58071c889574a3d5723c4363)
```
 - app/__init__.py
 - app/api/__init__.py
 - app/api/forward_openai.py
 - app/api/routes.py
 - app/api/sse.py
 - app/api/tools_api.py
 - app/core/__init__.py
 - app/core/config.py
 - app/core/http_client.py
 - app/core/logging.py
 - app/core/settings.py
 - app/http_client.py
 - app/main.py
 - app/manifests/__init__.py
 - app/manifests/tools_manifest.json
 - app/middleware/__init__.py
 - app/middleware/p4_orchestrator.py
 - app/middleware/relay_auth.py
 - app/middleware/validation.py
 - app/models/__init__.py
 - app/models/error.py
 - app/routes/__init__.py
 - app/routes/actions.py
 - app/routes/batches.py
 - app/routes/containers.py
 - app/routes/conversations.py
 - app/routes/embeddings.py
 - app/routes/files.py
 - app/routes/health.py
 - app/routes/images.py
 - app/routes/models.py
 - app/routes/proxy.py
 - app/routes/realtime.py
 - app/routes/register_routes.py
 - app/routes/responses.py
 - app/routes/uploads.py
 - app/routes/vector_stores.py
 - app/routes/videos.py
 - app/utils/__init__.py
 - app/utils/authy.py
 - app/utils/error_handler.py
 - app/utils/http_client.py
 - app/utils/logger.py
```

## TREE (tests/ at 3896cd6f44a7da6c58071c889574a3d5723c4363)
```
 - tests/__init__.py
 - tests/client.py
 - tests/conftest.py
 - tests/relay_client_example.py
 - tests/test_extended_routes_smoke_integration.py
 - tests/test_files_and_batches_integration.py
 - tests/test_images_variations_integration.py
 - tests/test_local_e2e.py
 - tests/test_realtime_ws_integration.py
 - tests/test_realtime_ws_local.py
 - tests/test_relay_auth_guard.py
 - tests/test_remaining_routes_smoke_integration.py
 - tests/test_sse_stream_open.py
 - tests/test_success_gates_integration.py
 - tests/test_videos_actions_integration.py
```

## TREE (static/ at 3896cd6f44a7da6c58071c889574a3d5723c4363)
```
 - static/.well-known/__init__.py
 - static/.well-known/ai-plugin.json
```

## TREE (schemas/ at 3896cd6f44a7da6c58071c889574a3d5723c4363)
```
 - schemas/__init__.py
 - schemas/openapi.yaml
```

## TREE (src/ at 3896cd6f44a7da6c58071c889574a3d5723c4363)
```
```

## TREE (scripts/src/ at 3896cd6f44a7da6c58071c889574a3d5723c4363)
```
```

## BASELINE (ROOT FILES)

## FILE: project-tree.md @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
  📄 .env.env
  📄 .env.example.env
  📄 .gitattributes
  📄 .gitignore
  📄 .gitleaks.toml
  📄 AGENTS.md
  📄 CONTRIBUTING.md
  📄 ChatGPT-API_reference_ground_truth-2025-10-29.pdf
  📄 Governence.md
  📄 P4_Cross_Domain_Analogy_Hybrid_Developer_v2_3_3.json
  📄 README.md
  📄 RELAY_CHECKLIST_v19.md
  📄 RELAY_PROGRESS_SUMMARY_v14.md
  📄 __init__.py
  📄 chatgpt_baseline.md
  📄 chatgpt_changes.md
  📄 chatgpt_sync.sh
  📄 generate_tree.py
  📄 openai_models_2025-11.csv
  📄 project-tree.md
  📄 pytest.ini
  📄 render.yaml
  📄 requirements.txt
  📁 .codex
  📁 app
    📄 __init__.py
    📄 http_client.py
    📄 main.py
    📁 api
      📄 __init__.py
      📄 forward_openai.py
      📄 routes.py
      📄 sse.py
      📄 tools_api.py
    📁 core
      📄 __init__.py
      📄 config.py
      📄 http_client.py
      📄 logging.py
      📄 settings.py
    📁 manifests
      📄 __init__.py
      📄 tools_manifest.json
    📁 middleware
      📄 __init__.py
      📄 p4_orchestrator.py
      📄 relay_auth.py
      📄 validation.py
    📁 models
      📄 __init__.py
      📄 error.py
    📁 routes
      📄 __init__.py
      📄 actions.py
      📄 batches.py
      📄 containers.py
      📄 conversations.py
      📄 embeddings.py
      📄 files.py
      📄 health.py
      📄 images.py
      📄 models.py
      📄 proxy.py
      📄 realtime.py
      📄 register_routes.py
      📄 responses.py
      📄 uploads.py
      📄 vector_stores.py
      📄 videos.py
    📁 utils
      📄 __init__.py
      📄 authy.py
      📄 error_handler.py
      📄 http_client.py
      📄 logger.py
  📁 chatgpt_team_relay.egg-info
    📄 PKG-INFO
    📄 SOURCES.txt
    📄 dependency_links.txt
    📄 requires.txt
    📄 top_level.txt
  📁 data
    📁 conversations
    📁 embeddings
      📄 embeddings.db
    📁 files
      📄 files.db
    📁 images
      📄 images.db
    📁 jobs
      📄 jobs.db
    📁 models
      📄 models.db
      📄 openai_models_categorized.csv
      📄 openai_models_categorized.json
    📁 uploads
      📄 attachments.db
      📄 file_9aa498e1dbb0
    📁 usage
      📄 usage.db
    📁 vector_stores
      📄 vectors.db
    📁 videos
      📄 videos.db
  📁 docs
    📄 README.md
  📁 path
    📁 to
      📄 input.png
  📁 schemas
    📄 __init__.py
    📄 openapi.yaml
  📁 scripts
    📄 README.md
    📄 batch_download_test.sh
    📄 content_endpoints_smoke.sh
    📄 coverage_report.sh
    📄 eval_p4_specs.py
    📄 images_variations_smoke.sh
    📄 make_sample_png.py
    📄 make_test_png.py
    📄 openapi_operationid_check.sh
    📄 run_success_gates.sh
    📄 smoke_images_variations.sh
    📄 sse_smoke_test.sh
    📄 test_31_endpoints.sh
    📄 test_local.sh
    📄 test_render.sh
    📄 test_success_gates_integration.py
    📄 uploads_e2e_test.sh
  📁 static
    📁 .well-known
      📄 __init__.py
      📄 ai-plugin.json
  📁 tests
    📄 __init__.py
    📄 client.py
    📄 conftest.py
    📄 relay_client_example.py
    📄 test_extended_routes_smoke_integration.py
    📄 test_files_and_batches_integration.py
    📄 test_images_variations_integration.py
    📄 test_local_e2e.py
    📄 test_realtime_ws_integration.py
    📄 test_realtime_ws_local.py
    📄 test_relay_auth_guard.py
    📄 test_remaining_routes_smoke_integration.py
    📄 test_success_gates_integration.py
    📄 test_videos_actions_integration.py```

## FILE: pyproject.toml @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "chatgpt-team-relay"
version = "0.1.0"
description = "OpenAI-compatible relay server for ChatGPT Team (FastAPI + OpenAI Python SDK)."
readme = "docs/README.md"
requires-python = ">=3.12"

dependencies = [
  "fastapi>=0.115,<1.0",
  "uvicorn[standard]>=0.32,<1.0",
  "httpx>=0.27,<1.0",

  "openai>=2.11.0,<3.0",

  "python-dotenv>=1.0,<2.0",
  "pydantic>=2.5,<3.0",
  "pydantic-settings>=2.2,<3.0",

  "python-multipart>=0.0.18,<0.1.0",
  "sse-starlette>=2.1,<3.0",

  "orjson>=3.9,<4.0",
  "pyyaml>=6.0,<7.0",
  "loguru>=0.7,<1.0",

  # Realtime WS proxy client
  "websockets>=12,<14",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3,<9.0",
  "pytest-asyncio>=0.23,<1.0",
  "pytest-env>=1.1,<2.0",
  "pytest-dotenv>=0.5,<1.0",
  "pytest-httpx>=0.30,<1.0",
  "pytest-mock>=3.14,<4.0",
  "requests>=2.32,<3.0",
  "requests-mock>=1.12,<2.0",
  "anyio>=4.4,<5.0",
]

[project.urls]
homepage = "https://github.com/virelai2604/chatgpt-team"
repository = "https://github.com/virelai2604/chatgpt-team"
issues = "https://github.com/virelai2604/chatgpt-team/issues"

# -----------------------------------------
# Setuptools: include ONLY app and app.*
# -----------------------------------------
[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]
exclude = ["tests*", "docs*", "render*"]

# Include non-.py files needed at runtime (tools manifest, etc.)
[tool.setuptools.package-data]
app = ["manifests/*.json"]
```

## FILE: chatgpt_sync.sh @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
#!/usr/bin/env bash
set -euo pipefail

# chatgpt_sync.sh (v4.3 - explicit allowlist + reliable NUL detection + UTF-16/UTF-32 BOM conversion)
#
# Purpose:
#   Generate Markdown artifacts that ChatGPT can ingest to get FULL current code/config text
#   for your repo, while avoiding secrets and noisy/generated artifacts.
#
# DEFAULT INCLUDED SCOPE (matches your requirement):
#   - Root files: pyproject.toml, project-tree.md
#   - Directories (recursive): app/, tests/, static/, schemas/
#
# Always EXCLUDED:
#   - Secrets: .env, .env.*, *.env, keys/certs
#   - Caches/artifacts: __pycache__/, *.pyc, venvs, logs, pytest caches, etc.
#   - Runtime state: data/ (and *.db / *.sqlite*)
#   - Generated outputs: chatgpt_sync.md, chatgpt_baseline.md, chatgpt_changes.md
#
# Modes:
#   baseline  -> embeds BASELINE content from a base commit (merge-base of HEAD and --base ref)
#   changes   -> shows diff vs base commit AND embeds CURRENT (worktree) content of changed files
#                (includes uncommitted edits)
#
# Examples:
#   ./chatgpt_sync.sh baseline --base origin/main --out chatgpt_baseline.md --max-bytes 2000000
#   ./chatgpt_sync.sh changes  --base origin/main --out chatgpt_changes.md  --max-bytes 2000000

MODE="${1:-}"
shift || true

BASE_REV="origin/main"
OUT_FILE="chatgpt_sync.md"
MAX_BYTES="2000000"
EMIT_TREE="true"

# Defaults: ONLY what you said matters
DIRS_DEFAULT=( "app" "tests" "static" "schemas" )
ROOT_FILES_DEFAULT=( "pyproject.toml" "project-tree.md" "chatgpt_sync.sh" "AGENTS.md" )

DIRS=()
ROOT_FILES=()

die() { echo "ERROR: $*" >&2; exit 1; }

usage() {
  cat >&2 <<'EOF'
Usage:
  ./chatgpt_sync.sh baseline|changes [flags]

Flags:
  --base <rev>        Base revision (default: origin/main)
  --out <file>        Output markdown file (default: chatgpt_sync.md)
  --max-bytes <n>     Max bytes per embedded text file (default: 2000000)
  --dir <path>        Include a directory (repeatable). If any --dir is provided, it replaces defaults.
  --root <file>       Include a root file (repeatable). If any --root is provided, it replaces defaults.
  --no-tree           Do not emit TREE sections
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base|--base-ref) BASE_REV="${2:-}"; shift 2 ;;
    --out) OUT_FILE="${2:-}"; shift 2 ;;
    --max-bytes) MAX_BYTES="${2:-}"; shift 2 ;;
    --dir)
      [[ -n "${2:-}" ]] || die "--dir requires a path"
      DIRS+=( "${2%/}" )
      shift 2
      ;;
    --root)
      [[ -n "${2:-}" ]] || die "--root requires a filename"
      ROOT_FILES+=( "$2" )
      shift 2
      ;;
    --no-tree) EMIT_TREE="false"; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

[[ "$MODE" == "baseline" || "$MODE" == "changes" ]] || { usage; die "First arg must be baseline or changes"; }
command -v git >/dev/null 2>&1 || die "git is required"
command -v sha256sum >/dev/null 2>&1 || die "sha256sum is required"
command -v python3 >/dev/null 2>&1 || die "python3 is required (for safe NUL detection)"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "Not in a git repo"
cd "$REPO_ROOT"

# Best-effort fetch so origin/main resolves
git fetch -q origin >/dev/null 2>&1 || true

BASE_COMMIT="$(git merge-base HEAD "$BASE_REV" 2>/dev/null || true)"
[[ -n "$BASE_COMMIT" ]] || die "Could not compute merge-base with base '$BASE_REV' (invalid ref?)"

NOW_ISO="$(date -Iseconds)"

if [[ "${#DIRS[@]}" -eq 0 ]]; then
  DIRS=( "${DIRS_DEFAULT[@]}" )
fi
if [[ "${#ROOT_FILES[@]}" -eq 0 ]]; then
  ROOT_FILES=( "${ROOT_FILES_DEFAULT[@]}" )
fi

is_denied_path() {
  local p="$1"
  case "$p" in
    .env|.env.*|*.env|*.key|*.pem|*.p12|*.pfx|*.crt|*.cer|*.der|*.jks|*.kdbx) return 0 ;;
    .venv/*|venv/*|__pycache__/*|*.pyc|*.pyo|*.log|.pytest_cache/*|.mypy_cache/*|.ruff_cache/*) return 0 ;;
    data/*|data) return 0 ;;
    chatgpt_sync.md|chatgpt_baseline.md|chatgpt_changes.md) return 0 ;;
  esac
  return 1
}

is_binary_ext() {
  local p="$1"
  case "$p" in
    *.pdf|*.png|*.jpg|*.jpeg|*.gif|*.zip|*.tar|*.gz|*.7z|*.whl|*.so|*.dylib|*.exe|*.db|*.sqlite|*.sqlite3|*.db-wal|*.db-shm|*.pyc) return 0 ;;
  esac
  return 1
}

# Returns 0 if file contains any NUL bytes, else 1.
has_nul_bytes() {
  local f="$1"
  python3 - "$f" <<'PY'
import sys
p = sys.argv[1]
with open(p, "rb") as fp:
    for chunk in iter(lambda: fp.read(1024 * 1024), b""):
        if b"\x00" in chunk:
            sys.exit(0)
sys.exit(1)
PY
}

maybe_convert_to_utf8_inplace() {
  local f="$1"

  # If no NUL bytes, treat as normal text.
  if ! has_nul_bytes "$f"; then
    return 0
  fi

  command -v iconv >/dev/null 2>&1 || return 1

  # Read BOM (first 4 bytes) to decide encoding.
  local bom
  bom="$(LC_ALL=C head -c 4 "$f" | od -An -tx1 | tr -d ' \n')"

  local enc=""
  case "$bom" in
    fffe*) enc="UTF-16LE" ;;
    feff*) enc="UTF-16BE" ;;
    0000feff) enc="UTF-32BE" ;;
    fffe0000) enc="UTF-32LE" ;;
    *) return 1 ;;
  esac

  local tmp
  tmp="$(mktemp)"
  if iconv -f "$enc" -t "UTF-8" "$f" >"$tmp" 2>/dev/null; then
    mv "$tmp" "$f"
  else
    rm -f "$tmp"
    return 1
  fi

  # After conversion, ensure no NULs remain.
  if has_nul_bytes "$f"; then
    return 1
  fi
  return 0
}

write_header() {
  cat <<EOF
# ChatGPT Sync
Repo: $(basename "$REPO_ROOT")
Base: ${BASE_REV}
Base commit (merge-base): ${BASE_COMMIT}
Dirs: ${DIRS[*]}
Root files: ${ROOT_FILES[*]}
Mode: ${MODE}
Generated: ${NOW_ISO}

EOF
}

emit_tree() {
  local commit="$1"

  echo "## TREE (repo root at ${commit})"
  echo '```'
  git ls-tree --name-only "$commit" | sed 's/^/ - /' || true
  echo '```'
  echo

  for d in "${DIRS[@]}"; do
    echo "## TREE (${d}/ at ${commit})"
    echo '```'
    git ls-tree -r --name-only "$commit" -- "$d" | sed 's/^/ - /' || true
    echo '```'
    echo
  done
}

record_blob_meta_at_commit() {
  local commit="$1"
  local path="$2"

  local size sha
  size="$(git cat-file -s "${commit}:${path}" 2>/dev/null || echo 0)"
  sha="$(git show "${commit}:${path}" 2>/dev/null | sha256sum | awk '{print $1}')"

  echo "## FILE: ${path} @ ${commit}"
  echo "> Not embedded (binary/large)."
  echo "> size_bytes: ${size}"
  echo "> sha256: ${sha}"
}

embed_text_blob_at_commit() {
  local commit="$1"
  local path="$2"

  local size
  size="$(git cat-file -s "${commit}:${path}" 2>/dev/null || echo 0)"

  if [[ "$size" -gt "$MAX_BYTES" ]]; then
    record_blob_meta_at_commit "$commit" "$path"
    return 0
  fi

  local tmp
  tmp="$(mktemp)"
  git show "${commit}:${path}" >"$tmp" 2>/dev/null || {
    rm -f "$tmp"
    echo "## FILE: ${path} @ ${commit}"
    echo "> Skipped: could not read."
    return 0
  }

  if ! maybe_convert_to_utf8_inplace "$tmp"; then
    rm -f "$tmp"
    record_blob_meta_at_commit "$commit" "$path"
    return 0
  fi

  echo "## FILE: ${path} @ ${commit}"
  echo '```'
  cat "$tmp"
  echo '```'
  rm -f "$tmp"
}

embed_worktree_file() {
  local path="$1"

  if is_denied_path "$path"; then
    echo "## FILE: ${path} @ WORKTREE"
    echo "> Skipped: denied by policy."
    return 0
  fi

  [[ -e "$path" ]] || { echo "## FILE: ${path} @ WORKTREE"; echo "> Skipped: missing."; return 0; }

  local size
  size="$(wc -c <"$path" | tr -d ' ')"

  if [[ "$size" -gt "$MAX_BYTES" ]] || is_binary_ext "$path"; then
    local sha
    sha="$(sha256sum "$path" | awk '{print $1}')"
    echo "## FILE: ${path} @ WORKTREE"
    echo "> Not embedded (binary/large)."
    echo "> size_bytes: ${size}"
    echo "> sha256: ${sha}"
    return 0
  fi

  local tmp
  tmp="$(mktemp)"
  cat "$path" >"$tmp" 2>/dev/null || { rm -f "$tmp"; echo "## FILE: ${path} @ WORKTREE"; echo "> Skipped: could not read."; return 0; }

  if ! maybe_convert_to_utf8_inplace "$tmp"; then
    rm -f "$tmp"
    local sha
    sha="$(sha256sum "$path" | awk '{print $1}')"
    echo "## FILE: ${path} @ WORKTREE"
    echo "> Not embedded (binary/large)."
    echo "> size_bytes: ${size}"
    echo "> sha256: ${sha}"
    return 0
  fi

  echo "## FILE: ${path} @ WORKTREE"
  echo '```'
  cat "$tmp"
  echo '```'
  rm -f "$tmp"
}

baseline_root() {
  local commit="$1"
  echo "## BASELINE (ROOT FILES)"
  echo

  for f in "${ROOT_FILES[@]}"; do
    is_denied_path "$f" && continue

    if git cat-file -e "${commit}:${f}" 2>/dev/null; then
      if is_binary_ext "$f"; then
        record_blob_meta_at_commit "$commit" "$f"
      else
        embed_text_blob_at_commit "$commit" "$f"
      fi
      echo
    else
      echo "## FILE: ${f} @ ${commit}"
      echo "> Missing at ${commit}"
      echo
    fi
  done
}

baseline_dirs() {
  local commit="$1"

  for d in "${DIRS[@]}"; do
    echo "## BASELINE (${d}/)"
    echo

    mapfile -t files < <(git ls-tree -r --name-only "$commit" -- "$d" || true)
    for f in "${files[@]}"; do
      is_denied_path "$f" && continue

      if is_binary_ext "$f"; then
        record_blob_meta_at_commit "$commit" "$f"
      else
        embed_text_blob_at_commit "$commit" "$f"
      fi
      echo
    done
  done
}

write_baseline() {
  write_header
  [[ "$EMIT_TREE" == "true" ]] && emit_tree "$BASE_COMMIT"
  baseline_root "$BASE_COMMIT"
  baseline_dirs "$BASE_COMMIT"
}

write_changes() {
  write_header

  local pathspec=()
  for d in "${DIRS[@]}"; do pathspec+=( "$d" ); done
  pathspec+=( "${ROOT_FILES[@]}" )

  local status patch
  status="$(git diff --name-status "${BASE_COMMIT}" -- "${pathspec[@]}" 2>/dev/null || true)"
  patch="$(git diff "${BASE_COMMIT}" -- "${pathspec[@]}" 2>/dev/null || true)"

  echo "## CHANGE SUMMARY (since ${BASE_COMMIT}, includes worktree)"
  echo
  if [[ -z "$status" ]]; then
    echo "> No changes detected in scope."
    echo
  else
    echo '```'
    echo "$status"
    echo '```'
    echo
  fi

  echo "## PATCH (since ${BASE_COMMIT}, includes worktree)"
  echo
  if [[ -z "$patch" ]]; then
    echo "> (empty)"
    echo
  else
    echo '```diff'
    echo "$patch"
    echo '```'
    echo
  fi

  echo "## CURRENT CONTENT OF CHANGED FILES (WORKTREE)"
  echo

  local changed_files=()
  if [[ -n "$status" ]]; then
    while IFS=$'\t' read -r st p1 p2; do
      [[ -n "${st:-}" ]] || continue

      if [[ "$st" =~ ^R ]]; then
        [[ -n "${p2:-}" ]] && changed_files+=( "$p2" )
        continue
      fi

      if [[ "$st" == "D" ]]; then
        echo "## FILE: ${p1} @ WORKTREE"
        echo "> Deleted in worktree."
        echo
        continue
      fi

      [[ -n "${p1:-}" ]] && changed_files+=( "$p1" )
    done <<<"$status"
  fi

  if [[ "${#changed_files[@]}" -eq 0 ]]; then
    echo "> No non-deleted changed files to embed."
    echo
    return 0
  fi

  for f in "${changed_files[@]}"; do
    embed_worktree_file "$f"
    echo
  done
}

tmp_out="$(mktemp)"
{
  if [[ "$MODE" == "baseline" ]]; then
    write_baseline
  else
    write_changes
  fi
} >"$tmp_out"

mv "$tmp_out" "$OUT_FILE"
echo "Wrote: ${REPO_ROOT}/${OUT_FILE}"
```

## FILE: AGENTS.md @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# Repository Guidelines – ChatGPT Team Relay (Codex Max / Custom Action Focus)

This AGENTS.md applies to the entire `chatgpt-team` repo. The primary goal is to use FastAPI + OpenAI APIs to power private ChatGPT Custom Actions for the owner/team, not to build a generic multi-user chat app.

---

## Baseline + Changes Contract (How you must read repo context)

I will provide you with two generated Markdown artifacts:

1) `chatgpt_baseline.md`
   - Authoritative baseline snapshot of the repo scope that matters.
   - Treat it as the codebase unless overridden by changes.

2) `chatgpt_changes.md`
   - Delta overlay on top of the baseline.
   - May include: change summary, unified diff patch, and full WORKTREE contents of changed files.

Rules:
- If the same file appears in both baseline and changes:
  - The version in `chatgpt_changes.md` is the latest truth.
- If a patch conflicts with embedded changed-file content:
  - Trust the embedded changed-file content and flag the inconsistency.
- Never invent missing files:
  - If a file is not present in baseline scope and not mentioned in changes, ask for the exact path.

Scope that matters long-term:
- repo root: `project-tree.md`, `pyproject.toml` (and optionally root `__init__.py`)
- directories: `app/`, `tests/`, `static/`, `schemas/`
Ignore everything else unless explicitly requested.

---

## Repo, Deployment & Environment

- GitHub (source of truth): https://github.com/virelai2604/chatgpt-team
- Primary deployment (Render): https://chatgpt-team-relay.onrender.com
- Primary workspace (WSL): `/home/user/code/chatgpt-team`
- Hosted relay endpoint (OpenAI-compatible): `https://chatgpt-team-relay.onrender.com/v1`

Runtime:
- Relay implements an OpenAI-compatible REST API.
- Default FastAPI app entrypoint: `app/main.py`.
- Primary routing and action logic lives in `app/routes/` and `app/api/`.
- Data files (SQLite, JSONL, temp artifacts) are under `data/` by convention and are not part of the long-term “action relay” scope unless explicitly needed.

Assumptions:
- This repository is a private glue layer between ChatGPT and OpenAI APIs on behalf of the owner.
- Prefer small, auditable changes; avoid adding heavy “chat app” features unless explicitly requested.

---

## OpenAI reference stack (priority: Website → GitHub → Local)

When generating or checking anything related to OpenAI APIs, models, tools, SDKs, or platform behavior, follow this priority order:

1) OpenAI platform docs (primary):
- https://platform.openai.com/docs/
- API reference: https://platform.openai.com/docs/api-reference/
- GPTs & Actions: https://platform.openai.com/docs/gpts/actions

2) Official OpenAI GitHub repos (secondary):
- Python SDK: https://github.com/openai/openai-python
- OpenAPI spec: https://github.com/openai/openai-openapi

3) Local PDF snapshot (tertiary, dated reference):
- `/home/user/code/chatgpt-team/ChatGPT-API_reference_ground_truth-2025-10-29.pdf`
- `\\wsl.localhost\\Ubuntu\\home\\user\\code\\chatgpt-team\\ChatGPT-API_reference_ground_truth-2025-10-29.pdf`

Conflict rule:
1) Website
2) Official GitHub
3) Local PDF
4) Third-party repos

If you detect changes versus older examples, spell it out explicitly instead of silently following stale behavior.

---

## Codex / Agent Behavior (P4 “Analogy Hybrid Developer”)

For any coding, design, or explanation task in this repo, use this response pattern:

1) Answer first — short, direct, correct.
2) Analogy — 1–2 lines from another domain (systems, science, nature).
3) Steps / Pseudocode / Code — clear algorithm, then full code when relevant.
4) How to Run/Test — exact commands, curl examples, or test cases.

Maintain:
- Professional, concise language.
- Strong preference for reproducible commands and tests.
- No filler.

---

## Project Overview

This repo is a FastAPI relay and automation layer between ChatGPT / GPT Actions and OpenAI APIs.

Main components:
- `app/main.py` — FastAPI entrypoint.
- `app/routes/` — HTTP routes, including Custom Action endpoints.
- `app/api/` — forwarding logic to OpenAI (or the relay provider), tools integration.
- `app/core/config.py` — environment variables, timeouts, default models.
- `schemas/openapi.yaml` — OpenAPI schema used by ChatGPT Actions.
- `tests/` — pytest suite validating routes, tools, and basic flows.

---

## Custom Action Focus

Goal: expose private ChatGPT Custom Actions powered by this relay.

Principles:
- Each Action = a clear API surface:
  - Validate input.
  - Call upstream (OpenAI / other tools).
  - Return a clean, typed response.
- No hidden side effects:
  - Avoid writing to DB unless explicitly requested.
  - Avoid long-running background jobs unless supported and documented.

When implementing or changing an Action:
1) Add/update route in `app/routes/actions.py` (or a clearly named module).
2) Update `schemas/openapi.yaml` so ChatGPT can discover the Action.
3) Add/update tests in `tests/` that cover:
   - Happy path.
   - Common error cases.
   - Basic schema/contract checks.

---

## Dev Environment & Commands (WSL)

Typical setup:

```bash
cd ~/code/chatgpt-team
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## FILE: __init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
```

## FILE: generate_tree.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
#!/usr/bin/env python3
"""
Clean Project Tree Generator
Generates a minimal, readable project structure with 📁 folders and 📄 files.
Outputs to `project-tree.md` at repo root.
"""

import os
from typing import List

# Excluded directories and file patterns (noise)
EXCLUDE_DIRS = {
    ".git", ".github", ".venv", "__pycache__", ".pytest_cache",
    "site-packages", "dist", "build", ".mypy_cache", ".idea", ".vscode",
}
EXCLUDE_FILES = {
    ".DS_Store", "Thumbs.db", "pyproject.toml", "Pipfile.lock",
}

OUTPUT_FILE = "project-tree.md"


def is_excluded(path: str) -> bool:
    parts = path.split(os.sep)
    return any(p in EXCLUDE_DIRS for p in parts)


def generate_tree(root_dir: str = ".") -> str:
    lines: List[str] = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter ignored dirs in place and sort for deterministic output
        dirnames[:] = sorted(
            d for d in dirnames
            if not is_excluded(os.path.join(dirpath, d))
        )

        if is_excluded(dirpath):
            continue

        depth = dirpath.count(os.sep)
        indent = "  " * depth
        dirname = os.path.basename(dirpath) or os.path.basename(os.path.abspath(root_dir))

        if dirpath != root_dir:
            lines.append(f"{indent}📁 {dirname}")

        sub_indent = "  " * (depth + 1)
        for filename in sorted(filenames):
            if filename in EXCLUDE_FILES:
                continue
            if filename.endswith((".pyc", ".pyo", ".log", ".tmp")):
                continue
            lines.append(f"{sub_indent}📄 {filename}")

    return "\n".join(lines)


def main() -> None:
    print("Generating clean project tree.")
    tree = generate_tree(".")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(tree)
    print(f"✅ Clean tree saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
```

## BASELINE (app/)

## FILE: app/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
```

## FILE: app/api/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
```

## FILE: app/api/forward_openai.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request, Response
from starlette.responses import StreamingResponse

from app.core.http_client import get_async_httpx_client
from app.core.settings import get_settings
from app.utils.logger import get_logger

_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

# Some upstream responses include these and Starlette will handle encoding itself.
_STRIP_RESPONSE_HEADERS = _HOP_BY_HOP_HEADERS | {
    "content-length",
    "content-encoding",
}

logger = get_logger(__name__)


def _get_timeout_seconds(settings: Any) -> float:
    # Settings uses timeout_seconds in your project; keep a defensive fallback.
    v = getattr(settings, "timeout_seconds", None)
    try:
        return float(v) if v is not None else 60.0
    except Exception:
        return 60.0


def _join_upstream_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


def _normalize_upstream_base(base: str, path: str) -> str:
    normalized = base.rstrip("/")
    if path.startswith("/v1") and normalized.endswith("/v1"):
        normalized = normalized[: -len("/v1")]
    return normalized
    

def _is_upload_parts_path(path: str) -> bool:
    return path.startswith("/v1/uploads/") and path.rstrip("/").endswith("/parts")


def _summarize_upstream_error(body: bytes, content_type: Optional[str]) -> str:
    if not body:
        return "empty body"

    payload = body.decode("utf-8", errors="replace")
    if content_type and "application/json" in content_type.lower():
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            error = parsed.get("error")
            if isinstance(error, dict):
                summary = {
                    "message": error.get("message"),
                    "type": error.get("type"),
                    "code": error.get("code"),
                    "param": error.get("param"),
                }
                return json.dumps(summary, ensure_ascii=False)

    return payload[:2000]


def _join_upstream_url_compat(*args: Any, **kwargs: Any) -> str:
    """
    Back-compat shim.

    Your SSE wiring previously called _join_upstream_url_compat() with 3 positional args,
    which must not crash the relay. We accept extra args and ignore them.
    """
    if len(args) >= 2:
        return _join_upstream_url(str(args[0]), str(args[1]))
    base = str(kwargs.get("base", "")).rstrip("/")
    path = str(kwargs.get("path", ""))
    return _join_upstream_url(base, path)


def build_upstream_url(
    path: str,
    *,
    request: Optional[Request] = None,
    query: Optional[Mapping[str, str]] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    Build the upstream URL (api.openai.com or configured base) + path + querystring.
    """
    settings = get_settings()
    base = (
        base_url
        or getattr(settings, "UPSTREAM_BASE_URL", None)
        or getattr(settings, "OPENAI_API_BASE", None)
        or "https://api.openai.com"
    )
    
    normalized_base = _normalize_upstream_base(str(base), path)
    url = _join_upstream_url(normalized_base, path)


    # Use explicit query override if provided; else forward inbound query params.
    q: Dict[str, str] = {}
    if query:
        q.update({str(k): str(v) for k, v in query.items()})
    elif request is not None:
        # request.query_params is MultiDict; best-effort collapse (tests only need wiring).
        for k, v in request.query_params.items():
            q[str(k)] = str(v)

    if q:
        url = f"{url}?{urlencode(q, doseq=True)}"

    return url


def build_outbound_headers(
    inbound_headers: Mapping[str, str],
    *,
    content_type: Optional[str] = None,
    forward_accept: bool = False,
    path_hint: Optional[str] = None,
) -> Dict[str, str]:
    """
    Copy inbound headers, strip hop-by-hop, and set upstream Authorization.
    """
    settings = get_settings()
    upstream_key = getattr(settings, "OPENAI_API_KEY", None)
    if not upstream_key:
        # If you hit this, your env is wrong; tests usually skip without a real key.
        raise HTTPException(status_code=424, detail="Missing OPENAI_API_KEY")

    out: Dict[str, str] = {}

    for k, v in inbound_headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk in {"host", "content-length"}:
            continue
        if lk == "authorization":
            continue
        if lk == "accept-encoding":
            continue
        out[k] = v
        
    out["Authorization"] = f"Bearer {upstream_key}"

    if content_type:
        for key in list(out.keys()):
            if key.lower() == "content-type":
                out.pop(key)  
        out["Content-Type"] = str(content_type)

    if forward_accept and "Accept" not in out and "accept" not in out:
        accept_header = inbound_headers.get("accept") or inbound_headers.get("Accept")
        if accept_header:
            out["Accept"] = accept_header

    out["Accept-Encoding"] = "identity"

    # Optional: forward OpenAI project/org headers if present in Settings (do not invent).
    org = getattr(settings, "OPENAI_ORG_ID", None) or getattr(settings, "OPENAI_ORGANIZATION", None)
    if org and "OpenAI-Organization" not in out:
        out["OpenAI-Organization"] = str(org)

    project = getattr(settings, "OPENAI_PROJECT", None)
    if project and "OpenAI-Project" not in out:
        out["OpenAI-Project"] = str(project)

    beta = getattr(settings, "OPENAI_ASSISTANTS_BETA", None)
    if beta and path_hint and path_hint.startswith("/v1/uploads"):
        out.setdefault("OpenAI-Beta", str(beta))
        
    return out


def filter_upstream_headers(inbound_headers: Mapping[str, str]) -> Dict[str, str]:
    # Backwards-compatible name used by containers.py
    return build_outbound_headers(inbound_headers)


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Strip hop-by-hop and Starlette-conflicting headers.
    """
    out: Dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in _STRIP_RESPONSE_HEADERS:
            continue
        out[k] = v
    return out


def _detect_wants_stream(*, accept_header: str, content_type: Optional[str], body_bytes: bytes) -> bool:
    if "text/event-stream" in (accept_header or "").lower():
        return True

    if content_type and "application/json" in content_type.lower():
        # Best-effort JSON parse to detect {"stream": true}
        try:
            obj = json.loads(body_bytes.decode("utf-8"))
            if isinstance(obj, dict) and obj.get("stream") is True:
                return True
        except Exception:
            pass

    return False


async def forward_openai_request(
    request: Request,
    *,
    upstream_path: Optional[str] = None,
    method: Optional[str] = None,
    query: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forward an incoming FastAPI Request to upstream OpenAI.

    Critical: get_async_httpx_client() returns an AsyncClient and must NOT be awaited.
    """
    settings = get_settings()
    upstream_path_final = upstream_path or request.url.path
    method_final = (method or request.method).upper()

    url = build_upstream_url(upstream_path_final, request=request, query=query)
    headers = build_outbound_headers(
        request.headers,
        path_hint=upstream_path_final,
        content_type=request.headers.get("content-type") if _is_upload_parts_path(upstream_path_final) else None,
    )

    body = await request.body()
    accept = request.headers.get("accept", "")
    content_type = request.headers.get("content-type")

    wants_stream = _detect_wants_stream(
        accept_header=accept,
        content_type=content_type,
        body_bytes=body,
    )

    client = get_async_httpx_client()
    timeout_s = _get_timeout_seconds(settings)

    if wants_stream:
        upstream_cm = client.stream(method_final, url, headers=headers, content=body, timeout=timeout_s)
        upstream_resp = await upstream_cm.__aenter__()

        async def _iter() -> Any:
            try:
                async for chunk in upstream_resp.aiter_bytes():
                    yield chunk
            finally:
                await upstream_cm.__aexit__(None, None, None)

        media_type = upstream_resp.headers.get("content-type") or "text/event-stream"
        return StreamingResponse(
            _iter(),
            status_code=upstream_resp.status_code,
            headers=_filter_response_headers(upstream_resp.headers),
            media_type=media_type,
        )

    try:
        upstream_resp = await client.request(
            method_final,
            url,
            headers=headers,
            content=body,
            timeout=timeout_s,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=424, detail=f"Upstream request failed: {type(e).__name__}: {e}") from e

    if _is_upload_parts_path(upstream_path_final) and upstream_resp.status_code >= 400:
        summary = _summarize_upstream_error(
            upstream_resp.content,
            upstream_resp.headers.get("content-type"),
        )
        logger.warning(
            "Upstream uploads parts error (%s) for %s: %s",
            upstream_resp.status_code,
            upstream_path_final,
            summary,
        )
    
    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=_filter_response_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
    )


async def forward_openai_method_path(
    method: str,
    path: str,
    *,
    json_body: Optional[Any] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
    request: Optional[Request] = None,
    query: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forward a synthetic request (method + path) to upstream OpenAI.

    Must accept positional (method, path) because routes call:
      forward_openai_method_path("POST", "/v1/responses", ...)

    This function may stream if:
      - inbound Accept includes text/event-stream, OR
      - json_body contains {"stream": true}
    """
    settings = get_settings()
    method_u = method.upper()
    url = build_upstream_url(path, request=request, query=query)

    headers = build_outbound_headers(inbound_headers or {}, path_hint=path)
    timeout_s = _get_timeout_seconds(settings)

    body_bytes: bytes = b""
    content_type = headers.get("Content-Type") or headers.get("content-type")

    if json_body is not None:
        body_bytes = json.dumps(json_body).encode("utf-8")
        # Ensure content-type for JSON bodies (unless caller already set it).
        if not content_type:
            headers["Content-Type"] = "application/json"
            content_type = "application/json"

    accept = (headers.get("Accept") or headers.get("accept") or "")
    wants_stream = _detect_wants_stream(
        accept_header=accept,
        content_type=content_type,
        body_bytes=body_bytes,
    )

    client = get_async_httpx_client()

    if wants_stream:
        upstream_cm = client.stream(method_u, url, headers=headers, content=body_bytes, timeout=timeout_s)
        upstream_resp = await upstream_cm.__aenter__()

        async def _iter() -> Any:
            try:
                async for chunk in upstream_resp.aiter_bytes():
                    yield chunk
            finally:
                await upstream_cm.__aexit__(None, None, None)

        media_type = upstream_resp.headers.get("content-type") or "text/event-stream"
        return StreamingResponse(
            _iter(),
            status_code=upstream_resp.status_code,
            headers=_filter_response_headers(upstream_resp.headers),
            media_type=media_type,
        )

    try:
        upstream_resp = await client.request(
            method_u,
            url,
            headers=headers,
            content=body_bytes,
            timeout=timeout_s,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=424, detail=f"Upstream request failed: {type(e).__name__}: {e}") from e

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=_filter_response_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
    )


async def forward_embeddings_create(
    body: Dict[str, Any],
    *,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """
    Convenience helper used by /v1/embeddings route.

    Returns JSON dict; raises HTTPException on upstream transport failures.
    """
    settings = get_settings()
    headers = build_outbound_headers(inbound_headers or {}, path_hint="/v1/embeddings")
    headers.setdefault("Content-Type", "application/json")

    client = get_async_httpx_client()
    timeout_s = _get_timeout_seconds(settings)

    try:
        url = build_upstream_url("/v1/embeddings")
        resp = await client.post(url, headers=headers, json=body, timeout=timeout_s)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=424, detail=f"Upstream request failed: {type(e).__name__}: {e}") from e

    # Even for non-2xx, OpenAI returns JSON error bodies; pass through as dict when possible.
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "body": resp.text}


# Back-compat/private aliases referenced by older SSE wiring (avoid import-time crashes).
_build_outbound_headers = build_outbound_headers
_filter_response_headers = _filter_response_headers
_join_upstream_url = _join_upstream_url
_join_upstream_url_compat = _join_upstream_url_compat
```

## FILE: app/api/routes.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import copy
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings

router = APIRouter()


def _build_manifest() -> Dict[str, Any]:
    s = get_settings()

    endpoints: Dict[str, list[str]] = {
        "health": ["/health", "/v1/health"],
        "models": ["/v1/models", "/v1/models/{model}"],
        "responses": [
            "/v1/responses",
            "/v1/responses/{response_id}",
            "/v1/responses/{response_id}/cancel",
            "/v1/responses/{response_id}/input_items",
        ],
        "responses_compact": ["/v1/responses/compact"],
        "responses_actions": ["/v1/actions/responses/stream"],
        "embeddings": ["/v1/embeddings"],
        "images": ["/v1/images/generations", "/v1/images/edits", "/v1/images/variations"],
        "images_actions": ["/v1/actions/images/edits", "/v1/actions/images/variations"],
        "proxy": ["/v1/proxy"],
        "realtime_http": ["/v1/realtime/sessions"],
        # NEW: Actions-friendly wrapper for multipart file upload
        "files_actions": ["/v1/actions/files/upload"],
        "uploads_actions": [
            "/v1/actions/uploads",
            "/v1/actions/uploads/{upload_id}/parts",
            "/v1/actions/uploads/{upload_id}/complete",
            "/v1/actions/uploads/{upload_id}/cancel",
        ],
        "videos_actions": [
            "/v1/actions/videos",
            "/v1/actions/videos/generations",
            "/v1/actions/videos/{video_id}/remix",
        ],
    }

    meta: Dict[str, Any] = {
        "relay_name": getattr(s, "RELAY_NAME", "chatgpt-team-relay"),
        "auth_required": bool(getattr(s, "RELAY_AUTH_ENABLED", False)),
        "auth_header": "X-Relay-Key",
        "upstream_base_url": getattr(s, "UPSTREAM_BASE_URL", getattr(s, "OPENAI_API_BASE", "")),
        "actions_openapi_url": "/openapi.actions.json",
        "actions_openapi_groups": [
            "health",
            "models",
            "responses",
            "responses_compact",
            "responses_actions",
            "embeddings",
            "images",
            "images_actions",
            "proxy",
            "realtime_http",
            
            # include wrapper routes in Actions schema
            "files_actions",
            "uploads_actions",
            "videos_actions",
        ],
    }

    return {
        "object": "relay.manifest",
        "data": {"endpoints": endpoints, "meta": meta},
        "endpoints": endpoints,
        "meta": meta,
    }


@router.get("/manifest", include_in_schema=False)
@router.get("/v1/manifest", include_in_schema=False)
async def get_manifest() -> Dict[str, Any]:
    return _build_manifest()


@router.get("/openapi.actions.json", include_in_schema=False)
async def openapi_actions(request: Request) -> JSONResponse:
    """
    Curated OpenAPI subset for ChatGPT Actions (REST; no WebSocket client).
    """
    full = request.app.openapi()
    manifest = _build_manifest()

    groups = (manifest.get("meta") or {}).get("actions_openapi_groups") or []
    endpoints = manifest.get("endpoints") or {}
    allowed_paths: set[str] = set()

    for g in groups:
        allowed_paths.update(endpoints.get(str(g), []) or [])

    allowed_paths.update({"/health", "/v1/health"})

    filtered = copy.deepcopy(full)
    filtered["paths"] = {
        p: spec for p, spec in (full.get("paths") or {}).items() if p in allowed_paths
    }

    info = filtered.get("info") or {}
    title = str(info.get("title") or "OpenAPI")
    info["title"] = f"{title} (Actions subset)"
    filtered["info"] = info

    return JSONResponse(filtered)
```

## FILE: app/api/sse.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from typing import Any, Dict, cast

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["sse"])
actions_router = APIRouter(prefix="/v1/actions/responses", tags=["responses_actions"])


@router.post("/responses:stream")
async def responses_stream(request: Request) -> Response:
    """
    Map POST /v1/responses:stream -> upstream POST /v1/responses with stream enabled.
    """
    body: Any = await request.json()
    if not isinstance(body, dict):
        body = {"input": body}

    body.setdefault("stream", True)

    return await forward_openai_method_path(
        request=request,
        method="POST",
        path="/v1/responses",
        inbound_headers=request.headers,
        json_body=cast(Dict[str, Any], body),
    )


@actions_router.post(
    "/stream",
    operation_id="actionsResponsesStream",
    summary="Actions wrapper for /v1/responses:stream (SSE)",
)
async def actions_responses_stream(request: Request) -> Response:
    """
    Actions-friendly SSE stream wrapper.

    Accepts JSON input and forwards to /v1/responses with stream enabled.
    """
    body: Any = await request.json()
    if not isinstance(body, dict):
        body = {"input": body}

    body.setdefault("stream", True)

    return await forward_openai_method_path(
        request=request,
        method="POST",
        path="/v1/responses",
        inbound_headers=request.headers,
        json_body=cast(Dict[str, Any], body),
    )```

## FILE: app/api/tools_api.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
#app/api/tools_api
from __future__ import annotations

import copy
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings

router = APIRouter()


def _build_manifest() -> Dict[str, Any]:
    s = get_settings()

    endpoints = {
        "health": ["/health", "/v1/health"],
        "models": ["/v1/models", "/v1/models/{model}"],
        "responses": [
            "/v1/responses",
            "/v1/responses/{response_id}",
            "/v1/responses/{response_id}/cancel",
            "/v1/responses/{response_id}/input_items",
        ],
        "responses_actions": ["/v1/actions/responses/stream"],
        "responses_compact": ["/v1/responses/compact"],
        "embeddings": ["/v1/embeddings"],
        "images": ["/v1/images/generations", "/v1/images/edits", "/v1/images/variations"],
        "images_actions": ["/v1/actions/images/edits", "/v1/actions/images/variations"],
        "files": ["/v1/files", "/v1/files/{file_id}", "/v1/files/{file_id}/content"],
        "files_actions": ["/v1/actions/files/upload"],
        "uploads_actions": [
            "/v1/actions/uploads",
            "/v1/actions/uploads/{upload_id}/parts",
            "/v1/actions/uploads/{upload_id}/complete",
            "/v1/actions/uploads/{upload_id}/cancel",
        ],
        "videos_actions": [
            "/v1/actions/videos",
            "/v1/actions/videos/generations",
            "/v1/actions/videos/{video_id}/remix",
        ],
        "uploads": [
            "/v1/uploads",
            "/v1/uploads/{upload_id}",
            "/v1/uploads/{upload_id}/parts",
            "/v1/uploads/{upload_id}/complete",
            "/v1/uploads/{upload_id}/cancel",
        ],
        "batches": ["/v1/batches", "/v1/batches/{batch_id}", "/v1/batches/{batch_id}/cancel"],
        "proxy": ["/v1/proxy"],
        "realtime_http": ["/v1/realtime/sessions"],
        "realtime_ws": ["/v1/realtime/ws"],
    }

    meta = {
        "relay_name": getattr(s, "RELAY_NAME", "chatgpt-team-relay"),
        "auth_required": bool(getattr(s, "RELAY_AUTH_ENABLED", False)),
        "auth_header": "X-Relay-Key",
        "upstream_base_url": getattr(s, "UPSTREAM_BASE_URL", getattr(s, "OPENAI_API_BASE", "")),
        "actions_openapi_url": "/openapi.actions.json",
        "actions_openapi_groups": [
            "health",
            "models",
            "responses",
            "responses_compact",
            "responses_actions",
            "embeddings",
            "images",
            "images_actions",
            "files_actions",
            "uploads_actions",
            "videos_actions",
            "proxy",
            "realtime_http",
        ],
    }

    # Provide both "old" and "new" shapes for compatibility:
    return {
        "object": "relay.manifest",
        "data": {"endpoints": endpoints, "meta": meta},
        "endpoints": endpoints,
        "meta": meta,
    }


@router.get("/manifest", include_in_schema=False)
@router.get("/v1/manifest", include_in_schema=False)
async def get_manifest() -> Dict[str, Any]:
    return _build_manifest()


@router.get("/openapi.actions.json", include_in_schema=False)
async def openapi_actions(request: Request) -> JSONResponse:
    """
    Curated OpenAPI subset for ChatGPT Actions (REST; no WebSocket client).
    """
    full = request.app.openapi()
    manifest = _build_manifest()

    groups = (manifest.get("meta") or {}).get("actions_openapi_groups") or []
    endpoints = manifest.get("endpoints") or {}
    allowed_paths: set[str] = set()

    for g in groups:
        allowed_paths.update(endpoints.get(str(g), []) or [])

    allowed_paths.update({"/health", "/v1/health"})

    filtered = copy.deepcopy(full)
    filtered["paths"] = {
        p: spec for p, spec in (full.get("paths") or {}).items() if p in allowed_paths
    }

    info = filtered.get("info") or {}
    title = str(info.get("title") or "OpenAPI")
    info["title"] = f"{title} (Actions subset)"
    filtered["info"] = info

    return JSONResponse(filtered)
```

## FILE: app/core/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
```

## FILE: app/core/config.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional


def _get_env(
    key: str,
    default: Optional[str] = None,
    *,
    required: bool = False,
) -> Optional[str]:
    """
    Read an environment variable as a string.

    - Treats unset or blank values as "missing".
    - If required=True and missing, raises RuntimeError.
    """
    value = os.getenv(key)
    if value is None:
        if required:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return default

    value = value.strip()
    if value == "":
        if required:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return default

    return value


def _get_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _get_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default

    raw = raw.strip().lower()
    if raw in ("1", "true", "t", "yes", "y", "on"):
        return True
    if raw in ("0", "false", "f", "no", "n", "off"):
        return False

    return default


def _parse_list(raw: str) -> List[str]:
    """
    Parse a list-like env var.

    Accepts:
      - JSON array:  '["a","b"]'
      - CSV:         'a,b'
      - Star:        '*'
    """
    raw = raw.strip()
    if raw == "":
        return []
    if raw == "*":
        return ["*"]

    # Prefer JSON arrays when provided.
    if raw.startswith("[") and raw.endswith("]"):
        try:
            val = json.loads(raw)
            if isinstance(val, list):
                return [str(x).strip() for x in val if str(x).strip() != ""]
        except Exception:
            # fall back to CSV parsing
            pass

    # CSV fallback
    return [item.strip() for item in raw.split(",") if item.strip()]


def _get_list(key: str, default: Optional[List[str]] = None) -> List[str]:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return list(default) if default is not None else []
    parsed = _parse_list(raw)
    if parsed:
        return parsed
    return list(default) if default is not None else []


@dataclass
class Settings:
    # Meta
    project_name: str

    # Core
    APP_MODE: str
    ENVIRONMENT: str

    # Logging
    LOG_LEVEL: str
    LOG_FORMAT: str
    LOG_COLOR: bool

    # OpenAI upstream
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str
    OPENAI_ASSISTANTS_BETA: str
    OPENAI_REALTIME_BETA: str
    OPENAI_ORGANIZATION: Optional[str]
    OPENAI_PROJECT: Optional[str]

    # Models
    DEFAULT_MODEL: str
    REALTIME_MODEL: str

    # Relay runtime
    RELAY_HOST: str
    RELAY_PORT: int
    RELAY_NAME: str
    RELAY_TIMEOUT: int
    PROXY_TIMEOUT: int
    PYTHON_VERSION: str
    RELAY_REALTIME_WS_ENABLED: bool

    # Streaming / orchestration
    ENABLE_STREAM: bool
    CHAIN_WAIT_MODE: str

    # Auth / secrets
    RELAY_AUTH_ENABLED: bool
    RELAY_KEY: Optional[str]
    CHATGPT_ACTIONS_SECRET: Optional[str]
    RELAY_AUTH_TOKEN: Optional[str]

    # CORS
    CORS_ALLOW_ORIGINS: List[str]
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]
    CORS_ALLOW_CREDENTIALS: bool

    # Tools / validation
    TOOLS_MANIFEST: str
    VALIDATION_SCHEMA_PATH: str

    # HTTP client behavior
    timeout_seconds: int
    max_retries: int

    # --------------------------
    # Compatibility aliases
    # --------------------------

    @property
    def app_mode(self) -> str:
        return self.APP_MODE

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @log_level.setter
    def log_level(self, value: str) -> None:
        self.LOG_LEVEL = value

    @property
    def relay_name(self) -> str:
        return self.RELAY_NAME

    @relay_name.setter
    def relay_name(self, value: str) -> None:
        self.RELAY_NAME = value

    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @openai_api_key.setter
    def openai_api_key(self, value: str) -> None:
        self.OPENAI_API_KEY = value

    @property
    def openai_base_url(self) -> str:
        return self.OPENAI_API_BASE

    @openai_base_url.setter
    def openai_base_url(self, value: str) -> None:
        self.OPENAI_API_BASE = value

    @property
    def openai_assistants_beta(self) -> str:
        return self.OPENAI_ASSISTANTS_BETA

    @property
    def openai_realtime_beta(self) -> str:
        return self.OPENAI_REALTIME_BETA

    @property
    def openai_organization(self) -> Optional[str]:
        return self.OPENAI_ORGANIZATION

    @property
    def openai_project(self) -> Optional[str]:
        return self.OPENAI_PROJECT

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @default_model.setter
    def default_model(self, value: str) -> None:
        self.DEFAULT_MODEL = value

    @property
    def realtime_model(self) -> str:
        return self.REALTIME_MODEL

    @realtime_model.setter
    def realtime_model(self, value: str) -> None:
        self.REALTIME_MODEL = value

    @property
    def relay_timeout_seconds(self) -> int:
        return self.RELAY_TIMEOUT

    @property
    def proxy_timeout_seconds(self) -> int:
        return self.PROXY_TIMEOUT

    @property
    def relay_auth_enabled(self) -> bool:
        return self.RELAY_AUTH_ENABLED

    @relay_auth_enabled.setter
    def relay_auth_enabled(self, value: bool) -> None:
        self.RELAY_AUTH_ENABLED = bool(value)

    @property
    def relay_key(self) -> Optional[str]:
        return self.RELAY_KEY

    @relay_key.setter
    def relay_key(self, value: Optional[str]) -> None:
        self.RELAY_KEY = value

    # Some modules expect this exact attribute name.
    @property
    def UPSTREAM_BASE_URL(self) -> str:
        return self.OPENAI_API_BASE

    @UPSTREAM_BASE_URL.setter
    def UPSTREAM_BASE_URL(self, value: str) -> None:
        self.OPENAI_API_BASE = value

    @property
    def tools_manifest(self) -> str:
        return self.TOOLS_MANIFEST

    @tools_manifest.setter
    def tools_manifest(self, value: str) -> None:
        self.TOOLS_MANIFEST = value

    @property
    def validation_schema_path(self) -> str:
        return self.VALIDATION_SCHEMA_PATH

    @validation_schema_path.setter
    def validation_schema_path(self, value: str) -> None:
        self.VALIDATION_SCHEMA_PATH = value

    @property
    def cors_allow_origins(self) -> List[str]:
        return self.CORS_ALLOW_ORIGINS

    @property
    def cors_allow_methods(self) -> List[str]:
        return self.CORS_ALLOW_METHODS

    @property
    def cors_allow_headers(self) -> List[str]:
        return self.CORS_ALLOW_HEADERS

    @property
    def cors_allow_credentials(self) -> bool:
        return self.CORS_ALLOW_CREDENTIALS

    @property
    def relay_realtime_ws_enabled(self) -> bool:
        return self.RELAY_REALTIME_WS_ENABLED


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_name = "chatgpt-team-relay"

    app_mode = _get_env("APP_MODE", "development") or "development"
    environment = _get_env("ENVIRONMENT", "development") or "development"

    log_level = (_get_env("LOG_LEVEL", "info") or "info").lower()
    log_format = _get_env("LOG_FORMAT", "console") or "console"
    log_color = _get_bool("LOG_COLOR", True)

    openai_api_base = _get_env("OPENAI_API_BASE", "https://api.openai.com") or "https://api.openai.com"
    # Allow empty key so the server can start; forwarder should reject requests if missing.
    openai_api_key = _get_env("OPENAI_API_KEY", "") or ""
    openai_assistants_beta = _get_env("OPENAI_ASSISTANTS_BETA", "assistants=v2") or "assistants=v2"
    openai_realtime_beta = _get_env("OPENAI_REALTIME_BETA", "realtime=v1") or "realtime=v1"
    openai_organization = os.getenv("OPENAI_ORGANIZATION")
    openai_project = os.getenv("OPENAI_PROJECT")

    default_model = _get_env("DEFAULT_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
    realtime_model = _get_env("REALTIME_MODEL", "gpt-4o-realtime-preview") or "gpt-4o-realtime-preview"

    relay_host = _get_env("RELAY_HOST", "0.0.0.0") or "0.0.0.0"
    relay_port = _get_int("RELAY_PORT", 8000)
    relay_name = _get_env("RELAY_NAME", "ChatGPT Team Relay (local dev)") or "ChatGPT Team Relay (local dev)"
    relay_timeout = _get_int("RELAY_TIMEOUT", 120)
    proxy_timeout = _get_int("PROXY_TIMEOUT", 120)
    python_version = _get_env("PYTHON_VERSION", "") or ""
    relay_realtime_ws_enabled = _get_bool("RELAY_REALTIME_WS_ENABLED", False)

    enable_stream = _get_bool("ENABLE_STREAM", True)
    chain_wait_mode = _get_env("CHAIN_WAIT_MODE", "sequential") or "sequential"

    relay_key = os.getenv("RELAY_KEY") or None
    relay_auth_token = os.getenv("RELAY_AUTH_TOKEN") or None
    chatgpt_actions_secret = os.getenv("CHATGPT_ACTIONS_SECRET")

    # Safer default: if RELAY_AUTH_ENABLED isn't set, enable it only when a key exists.
    relay_auth_enabled = _get_bool("RELAY_AUTH_ENABLED", bool(relay_key or relay_auth_token))

    cors_allow_origins = _get_list("CORS_ALLOW_ORIGINS", default=["*"])
    cors_allow_methods = _get_list("CORS_ALLOW_METHODS", default=["*"])
    cors_allow_headers = _get_list("CORS_ALLOW_HEADERS", default=["*"])
    cors_allow_credentials = _get_bool("CORS_ALLOW_CREDENTIALS", True)

    tools_manifest = _get_env("TOOLS_MANIFEST", "app/manifests/tools_manifest.json") or "app/manifests/tools_manifest.json"
    validation_schema_path = _get_env("VALIDATION_SCHEMA_PATH", "") or ""

    timeout_seconds = relay_timeout
    max_retries = _get_int("MAX_RETRIES", 3)

    return Settings(
        project_name=project_name,
        APP_MODE=app_mode,
        ENVIRONMENT=environment,
        LOG_LEVEL=log_level,
        LOG_FORMAT=log_format,
        LOG_COLOR=log_color,
        OPENAI_API_BASE=openai_api_base,
        OPENAI_API_KEY=openai_api_key,
        OPENAI_ASSISTANTS_BETA=openai_assistants_beta,
        OPENAI_REALTIME_BETA=openai_realtime_beta,
        OPENAI_ORGANIZATION=openai_organization,
        OPENAI_PROJECT=openai_project,
        DEFAULT_MODEL=default_model,
        REALTIME_MODEL=realtime_model,
        RELAY_HOST=relay_host,
        RELAY_PORT=relay_port,
        RELAY_NAME=relay_name,
        RELAY_TIMEOUT=relay_timeout,
        PROXY_TIMEOUT=proxy_timeout,
        PYTHON_VERSION=python_version,
        RELAY_REALTIME_WS_ENABLED=relay_realtime_ws_enabled,
        ENABLE_STREAM=enable_stream,
        CHAIN_WAIT_MODE=chain_wait_mode,
        RELAY_AUTH_ENABLED=relay_auth_enabled,
        RELAY_KEY=relay_key,
        CHATGPT_ACTIONS_SECRET=chatgpt_actions_secret,
        RELAY_AUTH_TOKEN=relay_auth_token,
        CORS_ALLOW_ORIGINS=cors_allow_origins,
        CORS_ALLOW_METHODS=cors_allow_methods,
        CORS_ALLOW_HEADERS=cors_allow_headers,
        CORS_ALLOW_CREDENTIALS=cors_allow_credentials,
        TOOLS_MANIFEST=tools_manifest,
        VALIDATION_SCHEMA_PATH=validation_schema_path,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )


settings: Settings = get_settings()
```

## FILE: app/core/http_client.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import asyncio
from typing import Optional

import httpx

from app.core.settings import get_settings

_async_httpx_client: Optional[httpx.AsyncClient] = None
_async_httpx_client_loop_id: Optional[int] = None


def get_async_httpx_client(*, timeout_seconds: float | None = None, timeout: float | None = None) -> httpx.AsyncClient:
    """
    Return a shared httpx.AsyncClient.

    Compatibility:
      - Some routes call get_async_httpx_client(timeout=...)
      - Other routes call get_async_httpx_client(timeout_seconds=...)

    We accept both and set the client timeout only at first construction.
    Per-request timeouts should be passed to client.request(..., timeout=...).
    """
    global _async_httpx_client, _async_httpx_client_loop_id

    # Prefer timeout_seconds; fall back to timeout; then Settings; then a safe default.
    settings = get_settings()
    initial_timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else timeout
        if timeout is not None
        else getattr(settings, "timeout_seconds", None)
        if getattr(settings, "timeout_seconds", None) is not None
        else 60.0
    )

    try:
        loop_id = id(asyncio.get_running_loop())
    except RuntimeError:
        loop_id = None

    if _async_httpx_client is None or _async_httpx_client.is_closed or _async_httpx_client_loop_id != loop_id:
        _async_httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(float(initial_timeout)),
            follow_redirects=False,
        )
        _async_httpx_client_loop_id = loop_id
        
    return _async_httpx_client
```

## FILE: app/core/logging.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
"""
Logging configuration module for the ChatGPT Team Relay.

This bridges the core config with the utility logger. The main entrypoint,
`configure_logging(settings)`, ensures that the global logger is set up
exactly once using the environment-driven values (LOG_LEVEL, LOG_FORMAT, etc.)
defined in :mod:`app.utils.logger`. It accepts a ``settings`` instance but does
not mutate or rely on it; the presence of ``settings`` in the signature
satisfies FastAPI/uvicorn calling conventions.

Consumers should import and call :func:`configure_logging` at application
startup to ensure consistent logging::

    from app.core.logging import configure_logging

    configure_logging(settings)

This design keeps logging configuration centralised while allowing easy
extension in the future.
"""

from __future__ import annotations

from typing import Any

# Importing from app.utils.logger will trigger root logger configuration on
# first call. See app/utils/logger.py for environment-driven behaviour.
from app.utils.logger import configure_logging as setup_logging
from app.utils.logger import get_logger


def configure_logging(settings: Any) -> None:
    """
    Initialise relay logging based on environment variables.

    This function calls into :func:`app.utils.logger.configure_logging` which
    configures the root logger using the environment variables ``LOG_LEVEL``,
    ``ERROR_LOG_PATH``, ``ERROR_LOG_MAX_BYTES``, and ``ERROR_LOG_BACKUP_COUNT``.
    It accepts a ``settings`` parameter for interface compatibility, but does
    not use it directly.

    Args:
        settings: settings object (unused but required for API compatibility).
    """
    setup_logging()
    get_logger("relay")
```

## FILE: app/core/settings.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

"""
Compatibility shim.

Some older modules referenced `app.core.settings`. The project centralizes settings in
`app.core.config`. This module re-exports the same symbols to avoid import breakage.
"""

from .config import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
```

## FILE: app/http_client.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

"""
Legacy re-export module.

Some earlier code imported `get_async_httpx_client` / `get_async_openai_client` from `app.http_client`.
The canonical implementation lives in `app.core.http_client`.
"""

from app.core.http_client import get_async_httpx_client, get_async_openai_client

__all__ = ["get_async_httpx_client", "get_async_openai_client"]
```

## FILE: app/main.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.sse import actions_router as sse_actions_router
from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes
from app.utils.logger import relay_log as logger


def _get_bool_setting(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "on"}:
            return True
        if v in {"0", "false", "no", "off"}:
            return False
    return default


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="chatgpt-team-relay",
        version="0.1.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        allow_credentials=_get_bool_setting(settings.CORS_ALLOW_CREDENTIALS, default=True),
    )

    # Always install relay auth middleware.
    # Whether it enforces auth is controlled at request-time (settings flags),
    # which is required for tests that monkeypatch settings without rebuilding the app.
    app.add_middleware(RelayAuthMiddleware)
    if getattr(settings, "RELAY_AUTH_ENABLED", False) and getattr(settings, "RELAY_KEY", ""):
        logger.info("Relay auth enabled (RELAY_AUTH_ENABLED=true).")
    else:
        logger.info("Relay auth disabled (RELAY_AUTH_ENABLED=false or RELAY_KEY missing).")

    # Register all route modules
    register_routes(app)

    # Tool manifest / helper endpoints
    app.include_router(tools_router)

    # SSE streaming endpoints (non-Actions + Actions wrapper)
    app.include_router(sse_router)
    app.include_router(sse_actions_router)

    return app


app = create_app()
```

## FILE: app/manifests/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# ==========================================================
# app/manifests/__init__.py — Ground Truth Manifest Loader
# ==========================================================
"""
Loads tools from app/manifests/tools_manifest.json and exposes TOOLS_MANIFEST.

Supports BOTH shapes:
  - {"tools": [ ... ]}   (original intention)
  - {"object":"list","data":[ ... ]} (your current file shape)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List


_manifest_path = os.path.join(os.path.dirname(__file__), "tools_manifest.json")


def _coerce_tools_list(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        return [t for t in raw if isinstance(t, dict)]

    if isinstance(raw, dict):
        tools = raw.get("tools")
        if isinstance(tools, list):
            return [t for t in tools if isinstance(t, dict)]

        data = raw.get("data")
        if isinstance(data, list):
            return [t for t in data if isinstance(t, dict)]

    return []


try:
    with open(_manifest_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    TOOLS_MANIFEST = _coerce_tools_list(raw)
except Exception as e:
    raise RuntimeError(f"Failed to load tools manifest: {_manifest_path} — {e}")
```

## FILE: app/manifests/tools_manifest.json @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
{
  "object": "list",
  "data": [
    {
      "id": "web_search",
      "name": "web_search",
      "object": "tool",
      "type": "function",
      "description": "Search the web for up-to-date information, news, and facts.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query string describing what to look up."
          },
          "recency_days": {
            "type": "integer",
            "description": "How many days back to prioritize in the search (e.g. 1 = last 24h, 7 = last week).",
            "minimum": 1,
            "default": 7
          },
          "max_results": {
            "type": "integer",
            "description": "Maximum number of search results to return.",
            "minimum": 1,
            "maximum": 20,
            "default": 5
          }
        },
        "required": ["query"]
      }
    },
    {
      "id": "file_search",
      "name": "file_search",
      "object": "tool",
      "type": "function",
      "description": "Search user-provided documents or vector stores to retrieve relevant passages.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Query string describing what information to retrieve from the files."
          },
          "top_k": {
            "type": "integer",
            "description": "Maximum number of chunks or documents to return.",
            "minimum": 1,
            "maximum": 50,
            "default": 8
          },
          "include_metadata": {
            "type": "boolean",
            "description": "Whether to return document metadata (file names, ids, etc.).",
            "default": true
          }
        },
        "required": ["query"]
      }
    },
    {
      "id": "image_generation",
      "name": "image_generation",
      "object": "tool",
      "type": "function",
      "description": "Generate images from natural language prompts using the images API.",
      "parameters": {
        "type": "object",
        "properties": {
          "prompt": {
            "type": "string",
            "description": "Detailed description of the image to generate."
          },
          "size": {
            "type": "string",
            "description": "Requested image size (for example, 512x512, 1024x1024).",
            "default": "1024x1024"
          },
          "n": {
            "type": "integer",
            "description": "Number of images to generate.",
            "minimum": 1,
            "maximum": 10,
            "default": 1
          }
        },
        "required": ["prompt"]
      }
    },
    {
      "id": "code_interpreter",
      "name": "code_interpreter",
      "object": "tool",
      "type": "function",
      "description": "Execute small code snippets (e.g. Python) for calculations, data inspection, and plotting.",
      "parameters": {
        "type": "object",
        "properties": {
          "language": {
            "type": "string",
            "description": "Programming language of the snippet (e.g. 'python').",
            "default": "python"
          },
          "code": {
            "type": "string",
            "description": "The code to execute."
          },
          "stdin": {
            "type": "string",
            "description": "Optional standard input for the process.",
            "nullable": true
          }
        },
        "required": ["code"]
      }
    },
    {
      "id": "mcp_connector",
      "name": "mcp_connector",
      "object": "tool",
      "type": "function",
      "description": "Call an MCP connector/server and invoke one of its tools.",
      "parameters": {
        "type": "object",
        "properties": {
          "server": {
            "type": "string",
            "description": "The MCP server or connector name to call."
          },
          "tool": {
            "type": "string",
            "description": "Tool name on the MCP server to invoke."
          },
          "arguments": {
            "type": "object",
            "description": "JSON object of arguments to pass to the selected tool.",
            "additionalProperties": true,
            "default": {}
          }
        },
        "required": ["server", "tool"]
      }
    },
    {
      "id": "apply_patch",
      "name": "apply_patch",
      "object": "tool",
      "type": "function",
      "description": "Apply structured patches to JSON or text documents (for example, configuration updates).",
      "parameters": {
        "type": "object",
        "properties": {
          "target": {
            "type": "string",
            "description": "Identifier of the target document or resource to patch."
          },
          "patch": {
            "type": "object",
            "description": "Patch payload describing the changes to apply.",
            "additionalProperties": true
          },
          "patch_type": {
            "type": "string",
            "description": "Type of patch to apply (e.g. json_merge, json_patch, text_replace).",
            "default": "json_merge"
          }
        },
        "required": ["target", "patch"]
      }
    },
    {
      "id": "shell",
      "name": "shell",
      "object": "tool",
      "type": "function",
      "description": "Execute shell commands in a controlled environment.",
      "parameters": {
        "type": "object",
        "properties": {
          "command": {
            "type": "string",
            "description": "Shell command to execute."
          },
          "timeout_seconds": {
            "type": "integer",
            "description": "Maximum time in seconds to allow the command to run.",
            "minimum": 1,
            "maximum": 300,
            "default": 60
          },
          "working_directory": {
            "type": "string",
            "description": "Optional working directory for the command.",
            "nullable": true
          }
        },
        "required": ["command"]
      }
    },
    {
      "id": "retrieval",
      "name": "retrieval",
      "object": "tool",
      "type": "function",
      "description": "High-level retrieval wrapper to fetch and synthesize information from multiple sources (files, vector stores, connectors).",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Natural language query describing the information to retrieve."
          },
          "sources": {
            "type": "array",
            "description": "List of logical sources to search over (e.g. ['files', 'web', 'mcp']).",
            "items": {
              "type": "string"
            },
            "default": ["files"]
          },
          "max_items": {
            "type": "integer",
            "description": "Maximum number of items to aggregate.",
            "minimum": 1,
            "maximum": 50,
            "default": 10
          }
        },
        "required": ["query"]
      }
    },
    {
      "id": "computer_use",
      "name": "computer_use",
      "object": "tool",
      "type": "function",
      "description": "Plan and issue high-level computer control actions (for example, open an app, click a button, type text).",
      "parameters": {
        "type": "object",
        "properties": {
          "action": {
            "type": "string",
            "description": "High-level action to perform (e.g. 'open_browser', 'click', 'type')."
          },
          "target": {
            "type": "string",
            "description": "The target element or application when applicable.",
            "nullable": true
          },
          "details": {
            "type": "object",
            "description": "Additional structured parameters for the action.",
            "additionalProperties": true,
            "default": {}
          }
        },
        "required": ["action"]
      }
    },
    {
      "id": "local_shell",
      "name": "local_shell",
      "object": "tool",
      "type": "function",
      "description": "Run shell commands against the local project environment (for example, git status, pytest).",
      "parameters": {
        "type": "object",
        "properties": {
          "command": {
            "type": "string",
            "description": "Command to run inside the local project workspace."
          },
          "timeout_seconds": {
            "type": "integer",
            "description": "Maximum runtime for the command.",
            "minimum": 1,
            "maximum": 300,
            "default": 60
          }
        },
        "required": ["command"]
      }
    }
  ]
}
```

## FILE: app/middleware/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
```

## FILE: app/middleware/p4_orchestrator.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# app/middleware/p4_orchestrator.py
import uuid
from typing import Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..utils.logger import get_logger

logger = get_logger(__name__)


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Simple correlation-ID and request logging middleware aligned with the P4 orchestration idea.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id

        logger.info(
            "Incoming request",
            extra={"path": str(request.url), "method": request.method, "request_id": request_id},
        )

        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
```

## FILE: app/middleware/relay_auth.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


# Paths that should remain reachable without relay auth:
# - health checks
# - OpenAPI + manifest (ChatGPT Actions)
# - docs (optional)
_PUBLIC_PATHS = {
    "/",
    "/health",
    "/v1/health",
    "/manifest",
    "/openapi.json",
    "/openapi.actions.json",
    "/docs",
    "/redoc",
}


def _extract_relay_key(request: Request) -> Optional[str]:
    # Preferred header
    x_key = request.headers.get("X-Relay-Key")
    if x_key:
        return x_key.strip()

    # Bearer fallback
    auth = (request.headers.get("Authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()

    return None


class RelayAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Public endpoints (no auth).
        if request.url.path in _PUBLIC_PATHS or request.url.path.startswith("/static/"):
            return await call_next(request)

        # If auth is disabled, do nothing.
        if not settings.RELAY_AUTH_ENABLED:
            return await call_next(request)

        # If Authorization exists but is not Bearer, return a message that includes "Bearer"
        # (tests assert this).
        auth = (request.headers.get("Authorization") or "").strip()
        if auth and not auth.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization must be Bearer <relay_key> (or use X-Relay-Key)."},
            )

        provided = _extract_relay_key(request)
        if not provided:
            return JSONResponse(status_code=401, content={"detail": "Missing relay key"})

        if provided != settings.RELAY_KEY:
            return JSONResponse(status_code=401, content={"detail": "Invalid relay key"})

        return await call_next(request)
```

## FILE: app/middleware/validation.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_415_UNSUPPORTED_MEDIA_TYPE

from app.core.logging import get_logger
from app.models.error import ErrorResponse

logger = get_logger(__name__)

_JSON_CT_PREFIX = "application/json"
_MULTIPART_CT_PREFIX = "multipart/form-data"


def _parse_content_length(value: str | None) -> int | None:
    """
    Parse Content-Length safely.

    Returns:
      - int (>=0) if parseable or empty-string treated as 0
      - None if not parseable
    """
    if value is None:
        return None

    v = value.strip()
    if v == "":
        # Some clients/proxies may send an empty Content-Length header.
        return 0

    # If multiple values appear (rare), take the first.
    first = v.split(",", 1)[0].strip()
    if first == "":
        return 0

    try:
        n = int(first)
        return max(n, 0)
    except ValueError:
        return None


def _has_body(request: Request) -> bool:
    """
    Determine if the request is expected to have a body without consuming it.

    Rules:
      - Content-Length parses to >0 => has body
      - Content-Length parses to 0 => no body
      - Transfer-Encoding present => has body
      - Otherwise => assume no body

    This is intentionally permissive for empty-body POSTs (e.g. cancel endpoints).
    """
    cl = _parse_content_length(request.headers.get("content-length"))
    if cl is not None:
        return cl > 0

    # Chunked uploads, etc.
    if request.headers.get("transfer-encoding"):
        return True

    return False


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Reject unsupported content-types for methods that typically carry bodies.

    IMPORTANT: allow empty-body requests (e.g., POST cancel endpoints) even if
    Content-Type is missing. Many clients send Content-Length: 0 and no CT.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method.upper()

        if method in {"POST", "PUT", "PATCH"} and _has_body(request):
            content_type = (request.headers.get("content-type") or "").strip()

            if not (
                content_type.startswith(_JSON_CT_PREFIX)
                or content_type.startswith(_MULTIPART_CT_PREFIX)
            ):
                msg = f"Unsupported Media Type: '{content_type}'"
                logger.info(
                    "ValidationMiddleware rejected request: method=%s path=%s content-type=%r content-length=%r",
                    request.method,
                    request.url.path,
                    content_type,
                    request.headers.get("content-length"),
                )
                err = ErrorResponse.from_message(msg)
                return err.to_response(status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        return await call_next(request)
```

## FILE: app/models/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from .error import ErrorDetail, ErrorResponse

__all__ = ["ErrorDetail", "ErrorResponse"]
```

## FILE: app/models/error.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from starlette.responses import JSONResponse


class ErrorDetail(BaseModel):
    message: str = Field(..., description="Human-readable error message.")
    type: str = Field(default="invalid_request_error", description="Error type.")
    param: Optional[str] = Field(default=None, description="Parameter related to the error, if any.")
    code: Optional[str] = Field(default=None, description="Machine-readable error code, if any.")


class ErrorResponse(BaseModel):
    error: ErrorDetail

    @classmethod
    def from_message(
        cls,
        message: str,
        *,
        type: str = "invalid_request_error",
        param: Optional[str] = None,
        code: Optional[str] = None,
    ) -> "ErrorResponse":
        return cls(error=ErrorDetail(message=message, type=type, param=param, code=code))

    def to_response(self, status_code: int = 400, headers: Optional[Dict[str, str]] = None) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content=self.model_dump(exclude_none=True),
            headers=headers,
        )
```

## FILE: app/routes/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# app/routes/__init__.py

from .register_routes import register_routes

__all__ = ["register_routes"]
```

## FILE: app/routes/actions.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# app/routes/actions.py

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter(tags=["actions"])


def _ping_payload() -> dict:
    """
    Canonical payload for ping-style endpoints.

    Tests assert at least:
      - data["status"] == "ok"            (for /actions/ping)
      - data["source"] == "chatgpt-team-relay"
      - data["app_mode"] non-empty
      - data["environment"] non-empty     (for /v1/actions/ping)
    """
    return {
        "source": "chatgpt-team-relay",
        "status": "ok",
        "app_mode": settings.APP_MODE,
        "environment": settings.ENVIRONMENT,
    }


def _relay_info_payloads() -> tuple[dict, dict]:
    """
    Build both the nested and flat relay-info payloads.

    Nested shape (for /v1/actions/relay_info):

        {
          "type": "relay.info",
          "relay": {
            "name": <relay_name>,
            "app_mode": <app_mode>,
            "environment": <environment>,
          },
          "upstream": {
            "base_url": <openai_base_url>,
            "default_model": <default_model>,
          },
        }

    Flat shape (for /actions/relay_info):

        {
          "relay_name": <relay_name>,
          "environment": <environment>,
          "app_mode": <app_mode>,
          "base_openai_api": <openai_base_url>,
        }

    The tests only assert that the relevant keys exist and are non-empty.
    """
    relay_name = settings.RELAY_NAME or "chatgpt-team-relay"
    app_mode = settings.APP_MODE
    environment = settings.ENVIRONMENT
    base_url = settings.OPENAI_API_BASE
    default_model = settings.DEFAULT_MODEL

    nested = {
        "type": "relay.info",
        "relay": {
            "name": relay_name,
            "app_mode": app_mode,
            "environment": environment,
        },
        "upstream": {
            "base_url": base_url,
            "default_model": default_model,
        },
    }

    flat = {
        "relay_name": relay_name,
        "environment": environment,
        "app_mode": app_mode,
        "base_openai_api": base_url,
    }

    return nested, flat


# ----- ping -----

@router.get("/actions/ping", summary="Simple local ping for tools/tests")
async def actions_ping_root() -> dict:
    """
    Simple ping at /actions/ping.

    tests/test_tools_and_actions_routes.py only checks that:
      - response.status_code == 200
      - response.json()["status"] == "ok"
    Extra fields are allowed.
    """
    return _ping_payload()


@router.get("/v1/actions/ping", summary="Local ping used by orchestrator tests")
async def actions_ping_v1() -> dict:
    """
    Ping under /v1/actions/ping.

    tests/test_actions_and_orchestrator.py requires:
      - status code 200
      - JSON contains non-empty source/status/app_mode/environment
    """
    return _ping_payload()


# ----- relay_info -----

@router.get("/actions/relay_info", summary="Flat relay info for tools")
async def actions_relay_info_root() -> dict:
    """
    Flat relay info at /actions/relay_info.

    tests/test_tools_and_actions_routes.py asserts:
      - data["relay_name"]
      - data["environment"]
      - data["app_mode"]
      - data["base_openai_api"]
    """
    _nested, flat = _relay_info_payloads()
    return flat


@router.get("/v1/actions/relay_info", summary="Structured relay info for orchestrator")
async def actions_relay_info_v1() -> dict:
    """
    Structured relay info at /v1/actions/relay_info.

    tests/test_actions_and_orchestrator.py asserts that:
      - data["type"] == "relay.info"
      - data["relay"]["name"] is non-empty
      - data["relay"]["app_mode"] is non-empty
      - data["relay"]["environment"] is non-empty
      - data["upstream"]["base_url"] is non-empty
      - data["upstream"]["default_model"] is non-empty
    """
    nested, _flat = _relay_info_payloads()
    return nested


@router.get("/actions/system/info", summary="Relay system info", include_in_schema=False)
async def system_info() -> JSONResponse:
    """
    Basic config info for debugging.

    NOTE: Not part of the official relay API; keep it local.
    """
    payload = {
        "relay_name": settings.RELAY_NAME,
        "app_mode": settings.APP_MODE,
        "environment": settings.ENVIRONMENT,
        "openai_api_base": settings.OPENAI_API_BASE,
        "default_model": settings.DEFAULT_MODEL,
        "openai_organization": settings.OPENAI_ORGANIZATION,
        "openai_project": settings.OPENAI_PROJECT,
        "openai_assistants_beta": settings.OPENAI_ASSISTANTS_BETA,
        "openai_realtime_beta": settings.OPENAI_REALTIME_BETA,
        "relay_auth_enabled": settings.RELAY_AUTH_ENABLED,
        "relay_auth_key_set": bool(settings.RELAY_KEY),
    }
    return JSONResponse(payload)
```

## FILE: app/routes/batches.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/v1/batches")
async def create_batch(request: Request) -> Response:
    logger.info("Incoming /v1/batches create request")
    return await forward_openai_request(request)


@router.get("/v1/batches/{batch_id}")
async def retrieve_batch(batch_id: str, request: Request) -> Response:
    logger.info(f"Incoming /v1/batches retrieve request for batch_id={batch_id}")
    return await forward_openai_request(request)


@router.get("/v1/batches")
async def list_batches(request: Request) -> Response:
    logger.info("Incoming /v1/batches list request")
    return await forward_openai_request(request)


@router.post("/v1/batches/{batch_id}/cancel")
async def cancel_batch(batch_id: str, request: Request) -> Response:
    logger.info(f"Incoming /v1/batches cancel request for batch_id={batch_id}")
    return await forward_openai_request(request)
```

## FILE: app/routes/containers.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse

from app.api.forward_openai import (
    _get_timeout_seconds,
    build_outbound_headers,
    build_upstream_url,
    filter_upstream_headers,
    forward_openai_request,
)
from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client

router = APIRouter(prefix="/v1", tags=["containers"])


@router.get("/containers")
async def containers_list(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/containers")
async def containers_create(request: Request) -> Response:
    return await forward_openai_request(request)


@router.head("/containers", include_in_schema=False)
async def containers_head(request: Request) -> Response:
    return await forward_openai_request(request)


@router.options("/containers", include_in_schema=False)
async def containers_options(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/containers/{container_id}/files/{file_id}/content")
async def containers_file_content(request: Request, container_id: str, file_id: str) -> Response:
    """
    Stream container file content.

    Critical behavior for Success Gate D:
      - Do NOT raise on upstream non-2xx.
      - If upstream returns 4xx/5xx, read the body and return it with upstream status
        (avoids relay 500 masking upstream errors).
      - Stream only on 2xx.
    """
    upstream_path = f"/v1/containers/{container_id}/files/{file_id}/content"

    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"

    upstream_url = build_upstream_url(upstream_path, request=request, base_url=base_url)

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    async with client.stream("GET", upstream_url, headers=headers) as upstream:
        status = upstream.status_code
        resp_headers = filter_upstream_headers(upstream.headers)
        media_type = upstream.headers.get("content-type")

        # IMPORTANT: never raise_for_status(); propagate upstream responses.
        if status >= 400:
            content = await upstream.aread()
            return Response(
                content=content,
                status_code=status,
                headers=resp_headers,
                media_type=media_type,
            )

        return StreamingResponse(
            upstream.aiter_bytes(),
            status_code=status,
            headers=resp_headers,
            media_type=media_type,
        )


@router.head("/containers/{container_id}/files/{file_id}/content", include_in_schema=False)
async def containers_file_content_head(request: Request, container_id: str, file_id: str) -> Response:
    return await forward_openai_request(request)
```

## FILE: app/routes/conversations.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["conversations"])


async def _forward(request: Request) -> Response:
    logger.info("→ [conversations] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# ---- /v1/conversations ----
@router.get("/conversations")
async def conversations_root_get(request: Request) -> Response:
    return await _forward(request)


@router.post("/conversations")
async def conversations_root_post(request: Request) -> Response:
    return await _forward(request)


@router.head("/conversations", include_in_schema=False)
async def conversations_root_head(request: Request) -> Response:
    return await _forward(request)


@router.options("/conversations", include_in_schema=False)
async def conversations_root_options(request: Request) -> Response:
    return await _forward(request)


# ---- /v1/conversations/{path:path} ----
@router.get("/conversations/{path:path}")
async def conversations_subpaths_get(path: str, request: Request) -> Response:
    return await _forward(request)


@router.post("/conversations/{path:path}")
async def conversations_subpaths_post(path: str, request: Request) -> Response:
    return await _forward(request)


@router.patch("/conversations/{path:path}")
async def conversations_subpaths_patch(path: str, request: Request) -> Response:
    return await _forward(request)


@router.delete("/conversations/{path:path}")
async def conversations_subpaths_delete(path: str, request: Request) -> Response:
    return await _forward(request)


@router.head("/conversations/{path:path}", include_in_schema=False)
async def conversations_subpaths_head(path: str, request: Request) -> Response:
    return await _forward(request)


@router.options("/conversations/{path:path}", include_in_schema=False)
async def conversations_subpaths_options(path: str, request: Request) -> Response:
    return await _forward(request)
```

## FILE: app/routes/embeddings.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.forward_openai import forward_embeddings_create

router = APIRouter(prefix="/v1", tags=["embeddings"])


@router.post("/embeddings")
async def create_embedding(request: Request) -> JSONResponse:
    body: Dict[str, Any] = await request.json()
    resp = await forward_embeddings_create(body)
    payload = resp.model_dump() if hasattr(resp, "model_dump") else resp
    return JSONResponse(content=payload)
```

## FILE: app/routes/files.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import base64
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response

from app.api.forward_openai import build_outbound_headers, build_upstream_url, forward_openai_method_path, forward_openai_request
from app.core.http_client import get_async_httpx_client
from app.core.settings import get_settings

router = APIRouter(prefix="/v1", tags=["files"])


def _filter_response_headers(headers: httpx.Headers) -> Dict[str, str]:
    """
    Strip hop-by-hop / conflicting headers to avoid Starlette issues.
    Keep this local to avoid relying on internal helpers.
    """
    strip = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",
        "content-encoding",
    }
    out: Dict[str, str] = {}
    for k, v in headers.items():
        if k.lower() in strip:
            continue
        out[k] = v
    return out


async def _is_user_data_file(file_id: str, request: Request) -> bool:
    """
    Best-effort guardrail:
    - If we can confirm purpose == 'user_data', block content download.
    - If we cannot confirm (metadata fetch fails), do not introduce new 5xx.
    """
    try:
        meta = await forward_openai_method_path(
            "GET",
            f"/v1/files/{file_id}",
            inbound_headers=request.headers,
        )
    except HTTPException:
        return False
    except Exception:
        return False

    return isinstance(meta, dict) and str(meta.get("purpose", "")).strip().lower() == "user_data"


@router.get("/files")
async def list_files(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/files")
async def create_file(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/files/{file_id}/content")
async def retrieve_file_content(file_id: str, request: Request) -> Response:
    if await _is_user_data_file(file_id, request):
        return JSONResponse(
            status_code=403,
            content={"detail": "Not allowed to download files with purpose 'user_data' via this relay."},
        )
    return await forward_openai_request(request)


class ActionsFileUploadRequest(BaseModel):
    """
    Actions-friendly file upload wrapper.

    Accept JSON + base64 to avoid multipart from Actions.
    """
    model_config = ConfigDict(extra="forbid")

    purpose: str = Field(..., description="Upstream file purpose (e.g. assistants)")
    filename: str = Field(..., description="Original filename (e.g. doc.pdf)")
    mime_type: str = Field(..., description="MIME type (e.g. application/pdf)")
    data_base64: str = Field(..., description="Base64-encoded file bytes (no data: prefix)")


@router.post(
    "/actions/files/upload",
    summary="Actions-friendly JSON->multipart wrapper for /v1/files",
    operation_id="actionsFilesUploadV1",
)
async def actions_files_upload(payload: ActionsFileUploadRequest, request: Request) -> Response:
    """
    Wrapper for multipart POST /v1/files:
      - Input: JSON with base64 bytes
      - Output: upstream JSON response (file object) or upstream error
    """
    # Size guard (base64 expands ~4/3). Keep conservative to reduce memory pressure.
    # You can raise this later if needed.
    max_bytes = 10 * 1024 * 1024  # 10 MiB decoded
    try:
        raw = base64.b64decode(payload.data_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 in data_base64")

    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="Empty file upload is not allowed")
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large for Actions wrapper (>{max_bytes} bytes)")

    upstream_path = "/v1/files"
    upstream_url = build_upstream_url(upstream_path, request=request)

    # Build auth + org/project headers; do NOT set Content-Type (httpx will set multipart boundary)
    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    settings = get_settings()
    timeout_s = float(getattr(settings, "timeout_seconds", 60.0) or 60.0)
    client = get_async_httpx_client(timeout=timeout_s)

    files = {
        "file": (payload.filename, raw, payload.mime_type),
    }
    data = {
        "purpose": payload.purpose,
    }

    try:
        resp = await client.post(upstream_url, headers=headers, data=data, files=files)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout while uploading file")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error while uploading file: {e!r}")

    # Return upstream response as-is (JSON error bodies included)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
        headers=_filter_response_headers(resp.headers),
    )
```

## FILE: app/routes/health.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


def _health_payload() -> Dict[str, Any]:
    """
    Health contract used by:
      - GET /
      - GET /health
      - GET /v1/health

    Tests expect:
      - object == "health"
      - status == "ok"
      - environment, default_model, timestamp keys
      - relay/openai/meta are dicts
    """
    now = datetime.now(timezone.utc).isoformat()

    environment = getattr(settings, "ENVIRONMENT", None) or getattr(settings, "APP_MODE", None) or "unknown"
    default_model = getattr(settings, "DEFAULT_MODEL", None) or "unknown"

    return {
        "object": "health",
        "status": "ok",
        "environment": environment,
        "default_model": default_model,
        "timestamp": now,
        "relay": {
            "app_mode": getattr(settings, "APP_MODE", None),
            "auth_enabled": bool(getattr(settings, "RELAY_AUTH_ENABLED", False)),
            "auth_header": getattr(settings, "RELAY_AUTH_HEADER", None),
            "relay_key_configured": bool(getattr(settings, "RELAY_KEY", None)),
        },
        "openai": {
            "base_url": getattr(settings, "OPENAI_BASE_URL", None),
            "api_key_configured": bool(getattr(settings, "OPENAI_API_KEY", None)),
        },
        "meta": {},
    }


@router.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    return _health_payload()


@router.get("/health")
async def health() -> Dict[str, Any]:
    return _health_payload()


@router.get("/v1/health")
async def v1_health() -> Dict[str, Any]:
    return _health_payload()
```

## FILE: app/routes/images.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# app/api/images.py
from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Mapping, Optional, Tuple
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import Response

from app.api.forward_openai import build_upstream_url, forward_openai_request
from app.core.config import get_settings
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["images"])
actions_router = APIRouter(prefix="/v1/actions/images", tags=["images_actions"])

# SSRF hardening: allow only OpenAI-controlled download hosts.
_ALLOWED_HOSTS_EXACT: set[str] = {
    "files.openai.com",
}
_ALLOWED_HOST_SUFFIXES: Tuple[str, ...] = (
    "oaiusercontent.com",
    "openai.com",
    "openaiusercontent.com",
)
_ALLOWED_AZURE_BLOBS_PREFIXES: Tuple[str, ...] = (
    "oaidalle",
    "oaidalleapiprod",
)

_MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4MB
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class OpenAIFileIdRef(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    mime_type: Optional[str] = Field(default=None, alias="mime_type")
    download_link: Optional[str] = None


class ImagesVariationsJSON(BaseModel):
    # Primary Actions file input
    openaiFileIdRefs: Optional[List[OpenAIFileIdRef]] = None

    # Fallbacks
    image_url: Optional[str] = None
    image_base64: Optional[str] = None

    # Standard params
    model: Optional[str] = None
    n: Optional[int] = None
    size: Optional[str] = None
    response_format: Optional[str] = None
    user: Optional[str] = None


class ImagesEditsJSON(BaseModel):
    openaiFileIdRefs: Optional[List[OpenAIFileIdRef]] = None

    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    mask_url: Optional[str] = None
    mask_base64: Optional[str] = None

    prompt: Optional[str] = None
    model: Optional[str] = None
    n: Optional[int] = None
    size: Optional[str] = None
    response_format: Optional[str] = None
    user: Optional[str] = None


def _is_multipart(request: Request) -> bool:
    ct = (request.headers.get("content-type") or "").lower()
    return ct.startswith("multipart/form-data")


def _validate_download_url(url: str) -> None:
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {exc}") from exc

    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only http/https URLs are supported")

    host = (parsed.hostname or "").lower()
    if not host:
        raise HTTPException(status_code=400, detail="Invalid URL host")

    if host in _ALLOWED_HOSTS_EXACT:
        return

    if any(host == s or host.endswith("." + s) for s in _ALLOWED_HOST_SUFFIXES):
        return

    # Allow specific OpenAI Azure blob hosts (tight pattern)
    if host.endswith("blob.core.windows.net") and any(host.startswith(p) for p in _ALLOWED_AZURE_BLOBS_PREFIXES):
        return

    raise HTTPException(status_code=400, detail="Refusing to fetch file URL from an untrusted host")


async def _download_bytes(url: str) -> bytes:
    _validate_download_url(url)

    timeout = httpx.Timeout(20.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=False) as client:
        async with client.stream("GET", url, headers={"Accept": "application/octet-stream"}) as resp:
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to download file (HTTP {resp.status_code})")

            buf = bytearray()
            async for chunk in resp.aiter_bytes():
                buf.extend(chunk)
                if len(buf) > _MAX_IMAGE_BYTES:
                    raise HTTPException(status_code=400, detail="Image exceeds 4 MB limit")
            return bytes(buf)


def _ensure_png(data: bytes, *, label: str) -> None:
    if not data.startswith(_PNG_MAGIC):
        raise HTTPException(status_code=400, detail=f"Uploaded {label} must be a PNG")


def _as_str_form_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _upstream_headers() -> Dict[str, str]:
    s = get_settings()
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {s.OPENAI_API_KEY}",
        "Accept": "application/json",
        "Accept-Encoding": "identity",
    }
    if s.OPENAI_ORGANIZATION:
        headers["OpenAI-Organization"] = s.OPENAI_ORGANIZATION
    if s.OPENAI_PROJECT:
        headers["OpenAI-Project"] = s.OPENAI_PROJECT
    return headers


async def _post_multipart_to_upstream(
    *,
    endpoint_path: str,  # must include /v1/...
    files: Dict[str, Tuple[str, bytes, str]],
    data: Dict[str, str],
) -> Response:
    s = get_settings()
    upstream_url = build_upstream_url(endpoint_path)
    timeout = httpx.Timeout(60.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        resp = await client.post(
            upstream_url,
            headers=_upstream_headers(),
            data=data,
            files=files,
        )

    content_type = resp.headers.get("content-type", "application/json")
    return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)


async def _build_variations_multipart(payload: ImagesVariationsJSON) -> Tuple[Dict[str, Tuple[str, bytes, str]], Dict[str, str]]:
    image_bytes: Optional[bytes] = None
    image_name = "image.png"

    # Prefer Actions file refs
    if payload.openaiFileIdRefs:
        first = payload.openaiFileIdRefs[0]
        if not first.download_link:
            raise HTTPException(status_code=400, detail="openaiFileIdRefs[0].download_link is required")
        image_bytes = await _download_bytes(first.download_link)
        image_name = first.name or image_name

    # Fallbacks
    if image_bytes is None and payload.image_url:
        image_bytes = await _download_bytes(payload.image_url)

    if image_bytes is None and payload.image_base64:
        try:
            image_bytes = base64.b64decode(payload.image_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid image_base64: {exc}") from exc

    if image_bytes is None:
        raise HTTPException(status_code=400, detail="Missing image input")

    _ensure_png(image_bytes, label="image")

    files = {"image": (image_name, image_bytes, "image/png")}

    form: Dict[str, str] = {}
    for k in ["model", "n", "size", "response_format", "user"]:
        v = getattr(payload, k)
        if v is not None:
            form[k] = _as_str_form_value(v)

    return files, form


async def _build_edits_multipart(payload: ImagesEditsJSON) -> Tuple[Dict[str, Tuple[str, bytes, str]], Dict[str, str]]:
    image_bytes: Optional[bytes] = None
    image_name = "image.png"

    mask_bytes: Optional[bytes] = None
    mask_name = "mask.png"

    if payload.openaiFileIdRefs:
        first = payload.openaiFileIdRefs[0]
        if not first.download_link:
            raise HTTPException(status_code=400, detail="openaiFileIdRefs[0].download_link is required")
        image_bytes = await _download_bytes(first.download_link)
        image_name = first.name or image_name

        if len(payload.openaiFileIdRefs) > 1:
            second = payload.openaiFileIdRefs[1]
            if second.download_link:
                mask_bytes = await _download_bytes(second.download_link)
                mask_name = second.name or mask_name

    if image_bytes is None and payload.image_url:
        image_bytes = await _download_bytes(payload.image_url)

    if image_bytes is None and payload.image_base64:
        try:
            image_bytes = base64.b64decode(payload.image_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid image_base64: {exc}") from exc

    if image_bytes is None:
        raise HTTPException(status_code=400, detail="Missing image input")

    _ensure_png(image_bytes, label="image")

    if mask_bytes is None and payload.mask_url:
        mask_bytes = await _download_bytes(payload.mask_url)

    if mask_bytes is None and payload.mask_base64:
        try:
            mask_bytes = base64.b64decode(payload.mask_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid mask_base64: {exc}") from exc

    if mask_bytes is not None:
        _ensure_png(mask_bytes, label="mask")

    files: Dict[str, Tuple[str, bytes, str]] = {"image": (image_name, image_bytes, "image/png")}
    if mask_bytes is not None:
        files["mask"] = (mask_name, mask_bytes, "image/png")

    form: Dict[str, str] = {}
    for k in ["prompt", "model", "n", "size", "response_format", "user"]:
        v = getattr(payload, k)
        if v is not None:
            form[k] = _as_str_form_value(v)

    return files, form


# --- Standard images routes ---


@router.post("/images", summary="Create image generation")
@router.post("/images/generations", summary="Create image generation (alias)")
async def create_image(request: Request) -> Response:
    logger.info("→ [images] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post(
    "/images/variations",
    summary="Create image variations (multipart or JSON wrapper)",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {"schema": ImagesVariationsJSON.model_json_schema()},
            }
        }
    },
)
async def variations_image(request: Request) -> Response:
    logger.info("→ [images] %s %s", request.method, request.url.path)

    if _is_multipart(request):
        return await forward_openai_request(request)

    body = await request.json()
    payload = ImagesVariationsJSON.model_validate(body)
    files, form = await _build_variations_multipart(payload)
    return await _post_multipart_to_upstream(endpoint_path="/v1/images/variations", files=files, data=form)


@router.post(
    "/images/edits",
    summary="Edit an image (multipart or JSON wrapper)",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {"schema": ImagesEditsJSON.model_json_schema()},
            }
        }
    },
)
async def edit_image(request: Request) -> Response:
    logger.info("→ [images] %s %s", request.method, request.url.path)

    if _is_multipart(request):
        return await forward_openai_request(request)

    body = await request.json()
    payload = ImagesEditsJSON.model_validate(body)
    files, form = await _build_edits_multipart(payload)
    return await _post_multipart_to_upstream(endpoint_path="/v1/images/edits", files=files, data=form)


# --- Actions-friendly aliases with clean JSON schemas ---


@actions_router.post("/variations", summary="Actions JSON wrapper for image variations")
async def actions_variations(payload: ImagesVariationsJSON) -> Response:
    files, form = await _build_variations_multipart(payload)
    return await _post_multipart_to_upstream(endpoint_path="/v1/images/variations", files=files, data=form)


@actions_router.post("/edits", summary="Actions JSON wrapper for image edits")
async def actions_edits(payload: ImagesEditsJSON) -> Response:
    files, form = await _build_edits_multipart(payload)
    return await _post_multipart_to_upstream(endpoint_path="/v1/images/edits", files=files, data=form)
```

## FILE: app/routes/models.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# app/routes/models.py

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# This router is mounted with prefix "/v1/models" in app.main
router = APIRouter(prefix="/v1/models", tags=["models"])


@router.get("")
async def list_models() -> dict:
    """
    Minimal, local implementation of GET /v1/models.

    For local development & integration tests we don't need to hit OpenAI.
    We just return a list with at least one model: settings.DEFAULT_MODEL.
    """
    default_id = settings.DEFAULT_MODEL

    logger.info("→ [models] local list /v1/models (default=%s)", default_id)

    return {
        "object": "list",
        "data": [
            {
                "object": "model",
                "id": default_id,
                "owned_by": "system",
            }
        ],
    }


@router.get("/{model_id}")
async def retrieve_model(model_id: str) -> dict:
    """
    Minimal, local implementation of GET /v1/models/{id}.

    Always returns a simple model object; tests only check:
      - body["object"] == "model"
      - body["id"] == requested id
    """
    logger.info("→ [models] local retrieve /v1/models/%s", model_id)

    return {
        "object": "model",
        "id": model_id,
        "owned_by": "system",
    }
```

## FILE: app/routes/proxy.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import re
from typing import Any, Dict, Optional, Set, Tuple

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["proxy"])


class ProxyRequest(BaseModel):
    """
    Action-friendly proxy envelope.

    Notes:
    - We intentionally do NOT use a field named `json`, because it shadows BaseModel.json().
    - For backward compatibility, we still ACCEPT an input key named "json" as an alias to `body`.
    """

    model_config = ConfigDict(extra="forbid")

    method: str = Field(..., description="HTTP method: GET, POST, PUT, PATCH, DELETE")
    path: str = Field(..., description="Upstream OpenAI path, e.g. /v1/responses")

    query: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices("query", "params", "query_params"),
        description="Query parameters (object/dict)",
    )

    body: Optional[Any] = Field(
        default=None,
        validation_alias=AliasChoices("body", "json", "json_body"),
        description="JSON body for POST/PUT/PATCH requests",
    )

    @model_validator(mode="after")
    def _avoid_empty_json_body_parse_errors(self) -> "ProxyRequest":
        m = (self.method or "").strip().upper()
        if m in {"POST", "PUT", "PATCH"} and self.body is None:
            self.body = {}
        return self


_ALLOWED_METHODS: Set[str] = {"GET", "POST", "PUT", "PATCH", "DELETE"}

_BLOCKED_PREFIXES: Tuple[str, ...] = (
    "/v1/admin",
    "/v1/webhooks",
    "/v1/moderations",
    "/v1/realtime",  # websocket family (not Actions-friendly)
    "/v1/uploads",  # multipart/resumable (use explicit wrapper routes)
    "/v1/audio",  # often multipart/binary
)

_BLOCKED_PATHS: Set[str] = {
    "/v1/proxy",
    "/v1/responses:stream",
}

_BLOCKED_SUFFIXES: Tuple[str, ...] = (
    "/content",
    "/results",
)

_BLOCKED_METHOD_PATH_REGEX: Set[Tuple[str, re.Pattern[str]]] = {
    ("POST", re.compile(r"^/v1/files$")),
    ("POST", re.compile(r"^/v1/images/(edits|variations)$")),
    ("POST", re.compile(r"^/v1/videos$")),  # create video is multipart/form-data
}

# Allowlist: (methods, regex)
_ALLOWLIST: Tuple[Tuple[Set[str], re.Pattern[str]], ...] = (
    # ---- Responses (JSON) ----
    ({"POST"}, re.compile(r"^/v1/responses$")),
    ({"POST"}, re.compile(r"^/v1/responses/compact$")),
    ({"GET"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+$")),
    ({"DELETE"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+$")),
    ({"POST"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+/cancel$")),
    ({"GET"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+/input_items$")),
    ({"POST"}, re.compile(r"^/v1/responses/input_tokens$")),

    # ---- Embeddings (JSON) ----
    ({"POST"}, re.compile(r"^/v1/embeddings$")),

    # ---- Models (JSON) ----
    ({"GET"}, re.compile(r"^/v1/models$")),
    ({"GET"}, re.compile(r"^/v1/models/[^/]+$")),

    # ---- Images (JSON only: generations) ----
    ({"POST"}, re.compile(r"^/v1/images/generations$")),
    ({"POST"}, re.compile(r"^/v1/images$")),

    # ---- Videos (metadata only via proxy; content is binary, create is multipart) ----
    ({"GET"}, re.compile(r"^/v1/videos$")),
    ({"GET"}, re.compile(r"^/v1/videos/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/videos/[^/]+$")),

    # ---- Vector Stores (JSON) ----
    ({"GET"}, re.compile(r"^/v1/vector_stores$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores$")),
    ({"PUT"}, re.compile(r"^/v1/vector_stores$")),
    ({"PATCH"}, re.compile(r"^/v1/vector_stores$")),
    ({"DELETE"}, re.compile(r"^/v1/vector_stores$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/search$")),
    ({"PUT"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"PATCH"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    
    # vector store files
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/files$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/files$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),

    # vector store file batches
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+/cancel$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+/files$")),

    # ---- Containers (JSON control plane only) ----
    ({"GET"}, re.compile(r"^/v1/containers$")),
    ({"POST"}, re.compile(r"^/v1/containers$")),
    ({"GET"}, re.compile(r"^/v1/containers/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/containers/[^/]+$")),

    # ---- Conversations (JSON) ----
    ({"POST"}, re.compile(r"^/v1/conversations$")),
    ({"GET"}, re.compile(r"^/v1/conversations$")),
    ({"GET"}, re.compile(r"^/v1/conversations/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/conversations/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/conversations/[^/]+$")),

    # ---- Files (JSON metadata only; content is binary; create is multipart) ----
    ({"GET"}, re.compile(r"^/v1/files$")),
    ({"GET"}, re.compile(r"^/v1/files/[A-Za-z0-9_-]+$")),
    ({"DELETE"}, re.compile(r"^/v1/files/[A-Za-z0-9_-]+$")),
    ({"GET"}, re.compile(r"^/v1/files/[A-Za-z0-9_-]+$")),
    ({"DELETE"}, re.compile(r"^/v1/files/[A-Za-z0-9_-]+$")),
    
    # ---- Batches (JSON) ----
    ({"GET"}, re.compile(r"^/v1/batches$")),
    ({"POST"}, re.compile(r"^/v1/batches$")),
    ({"GET"}, re.compile(r"^/v1/batches/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/batches/[^/]+/cancel$")),
)


def _normalize_path(path: str) -> str:
    p = (path or "").strip()
    if not p:
        raise HTTPException(status_code=400, detail="path is required")

    if "://" in p or p.lower().startswith("http"):
        raise HTTPException(status_code=400, detail="path must be an OpenAI API path, not a URL")

    if "?" in p:
        raise HTTPException(status_code=400, detail="path must not include '?'; use `query` field")

    if not p.startswith("/"):
        p = "/" + p

    if p.startswith("/v1"):
        normalized = p
    elif p.startswith("v1/"):
        normalized = "/" + p
    else:
        normalized = "/v1" + p

    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    return normalized


def _blocked_reason(method: str, path: str, body: Any) -> Optional[str]:
    if isinstance(body, dict) and body.get("stream") is True:
        return "stream=true is not allowed via /v1/proxy (use explicit streaming route)"

    if ":" in path:
        return "':' paths are not allowed via /v1/proxy"

    if ".." in path or "#" in path:
        return "path contains illegal sequences"
    if any(ch.isspace() for ch in path):
        return "path must not contain whitespace"

    if path in _BLOCKED_PATHS:
        return "path is blocked"

    for prefix in _BLOCKED_PREFIXES:
        if path.startswith(prefix):
            return f"blocked prefix: {prefix}"

    for suffix in _BLOCKED_SUFFIXES:
        if path.endswith(suffix):
            return f"blocked suffix: {suffix}"

    for (m, rx) in _BLOCKED_METHOD_PATH_REGEX:
        if method == m and rx.match(path):
            return "multipart endpoint blocked via /v1/proxy"

    return None


def _is_allowlisted(method: str, path: str) -> bool:
    for methods, rx in _ALLOWLIST:
        if method in methods and rx.match(path):
            return True
    return False


@router.post("/proxy")
async def proxy(call: ProxyRequest, request: Request) -> Response:
    method = (call.method or "").strip().upper()
    if method not in _ALLOWED_METHODS:
        raise HTTPException(status_code=400, detail=f"Unsupported method: {call.method}")

    path = _normalize_path(call.path)

    reason = _blocked_reason(method, path, call.body)
    if reason:
        raise HTTPException(status_code=403, detail={"error": reason})

    if not _is_allowlisted(method, path):
        raise HTTPException(status_code=403, detail="method/path not allowlisted for /v1/proxy")

    return await forward_openai_method_path(
        method=method,
        path=path,
        query=call.query,
        json_body=call.body,
        inbound_headers=request.headers,
    )
```

## FILE: app/routes/realtime.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# app/routes/realtime.py

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode, urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from websockets import connect as ws_connect  # type: ignore
from websockets.exceptions import ConnectionClosed  # type: ignore

from app.core.config import get_settings
from app.utils.logger import relay_log as logger


def _normalize_openai_api_base(raw: str) -> str:
    base = raw.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base


RAW_OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_API_BASE_SOURCE = "env:OPENAI_API_BASE" if RAW_OPENAI_API_BASE else "default:https://api.openai.com"
OPENAI_API_BASE = _normalize_openai_api_base(RAW_OPENAI_API_BASE or "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA", "realtime=v1")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
DEFAULT_REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-realtime")
ALLOWED_REALTIME_MODELS = {
    "gpt-realtime-mini-2025-12-15",
    "gpt-realtime",
    "gpt-realtime-2025-08-28",
    "gpt-realtime-mini",
    "gpt-realtime-mini-2025-10-06",
}

router = APIRouter(
    prefix="/v1",
    tags=["realtime"],
)


def _build_headers(request: Request | None = None) -> Dict[str, str]:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured for Realtime sessions",
                    "type": "config_error",
                    "code": "no_api_key",
                }
            },
        )

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    incoming_beta = request.headers.get("OpenAI-Beta") if request else None
    beta = incoming_beta or OPENAI_REALTIME_BETA
    if beta:
        headers["OpenAI-Beta"] = beta

    return headers


def _realtime_upstream_context() -> Dict[str, Any]:
    return {
        "openai_api_base": OPENAI_API_BASE,
        "openai_api_base_source": OPENAI_API_BASE_SOURCE,
        "realtime_sessions_url": f"{OPENAI_API_BASE}/v1/realtime/sessions",
    }


def _resolve_port(scheme: Optional[str], port: Optional[int]) -> Optional[int]:
    if port is not None:
        return port
    if scheme == "https":
        return 443
    if scheme == "http":
        return 80
    return None


def _validate_realtime_upstream(request: Request) -> None:
    url = f"{OPENAI_API_BASE}/v1/realtime/sessions"
    parsed_base = urlparse(OPENAI_API_BASE)
    context = _realtime_upstream_context()
    settings = get_settings()

    if parsed_base.scheme not in ("http", "https") or not parsed_base.hostname:
        logger.error("Invalid realtime upstream base: %s", context)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "Invalid OPENAI_API_BASE for realtime sessions",
                    "type": "config_error",
                    "code": "invalid_api_base",
                    "extra": context,
                }
            },
        )

    relay_host = request.url.hostname
    if relay_host and parsed_base.hostname == relay_host:
        relay_port = _resolve_port(request.url.scheme, request.url.port)
        upstream_port = _resolve_port(parsed_base.scheme, parsed_base.port)
        if upstream_port is None or relay_port == upstream_port:
            loop_context = {
                **context,
                "relay_host": relay_host,
                "relay_port": relay_port,
                "upstream_host": parsed_base.hostname,
                "upstream_port": upstream_port,
            }
            logger.error("Realtime upstream base would loop to relay: %s", loop_context)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "message": "OPENAI_API_BASE resolves to the relay host and would cause a proxy loop",
                        "type": "config_error",
                        "code": "realtime_base_loop",
                        "extra": loop_context,
                    }
                },
            )

    if settings.RELAY_HOST and parsed_base.hostname == settings.RELAY_HOST:
        relay_port = _resolve_port(request.url.scheme, settings.RELAY_PORT)
        upstream_port = _resolve_port(parsed_base.scheme, parsed_base.port)
        if upstream_port is None or relay_port == upstream_port:
            loop_context = {
                **context,
                "relay_host": settings.RELAY_HOST,
                "relay_port": relay_port,
                "upstream_host": parsed_base.hostname,
                "upstream_port": upstream_port,
            }
            logger.error("Realtime upstream base matches relay settings: %s", loop_context)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "message": "OPENAI_API_BASE matches relay host settings and would cause a proxy loop",
                        "type": "config_error",
                        "code": "realtime_base_loop_settings",
                        "extra": loop_context,
                    }
                },
            )


async def _post_realtime_sessions(
    request: Request,
    body: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """
    Helper for POST {OPENAI_API_BASE}/v1/realtime/sessions
    """
    _validate_realtime_upstream(request)
    url = f"{OPENAI_API_BASE}/v1/realtime/sessions"

    headers = _build_headers(request)
    timeout = httpx.Timeout(PROXY_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, headers=headers, json=body or {})
        except httpx.RequestError as exc:
            logger.error("Error calling OpenAI Realtime sessions: %r", exc)
            context = _realtime_upstream_context()
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": "Error calling OpenAI Realtime sessions",
                        "type": "server_error",
                        "code": "upstream_request_error",
                        "extra": {"exception": str(exc), **context},
                    }
                },
            ) from exc

    try:
        data = resp.json()
    except json.JSONDecodeError:
        data = {"raw": resp.text}

    return resp.status_code, data


@router.post("/realtime/sessions")
async def create_realtime_session(request: Request) -> JSONResponse:
    """
    POST /v1/realtime/sessions – create a Realtime session descriptor.

    If the client omits `model`, we default to REALTIME_MODEL.
    """
    try:
        payload: Any = await request.json()
    except Exception:
        payload = {}

    if not isinstance(payload, dict):
        payload = {}

    payload.pop("expires_at", None)

    payload.setdefault("model", DEFAULT_REALTIME_MODEL)
    model = payload.get("model")

    if model not in ALLOWED_REALTIME_MODELS:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "message": "Unsupported realtime model",
                    "type": "invalid_request_error",
                    "code": "unsupported_model",
                    "param": "model",
                    "extra": {
                        "model": model,
                        "allowed": sorted(ALLOWED_REALTIME_MODELS),
                    },
                }
            },
        )

    status_code, data = await _post_realtime_sessions(request, payload)
    if status_code >= 400:
        upstream_url = f"{OPENAI_API_BASE}/v1/realtime/sessions"
        logger.warning(
            "Realtime session upstream error: status=%s base=%s url=%s source=%s",
            status_code,
            OPENAI_API_BASE,
            upstream_url,
            OPENAI_API_BASE_SOURCE,
        )
        if not isinstance(data, dict):
            data = {"error": {"message": "Realtime upstream error", "type": "upstream_error"}}
        error = data.get("error")
        if not isinstance(error, dict):
            error = {"message": "Realtime upstream error", "type": "upstream_error"}
        extra = error.get("extra")
        if not isinstance(extra, dict):
            extra = {}
        extra.update(
            {
                "openai_api_base": OPENAI_API_BASE,
                "openai_api_base_source": OPENAI_API_BASE_SOURCE,
                "realtime_sessions_url": upstream_url,
            }
        )
        error["extra"] = extra
        data["error"] = error
    return JSONResponse(status_code=status_code, content=data)


class RealtimeSessionValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., description="Realtime session ID to validate")
    expires_at: Optional[float] = Field(
        default=None,
        description="Optional Unix timestamp (seconds) for session expiry",
    )


@router.post("/realtime/sessions/validate")
async def validate_realtime_session(payload: RealtimeSessionValidateRequest) -> JSONResponse:
    """
    Local-only validation helper for realtime session descriptors.

    Stateless; does not call upstream. Validates shape and expiry.
    """
    now = time.time()
    if payload.expires_at is not None and payload.expires_at <= now:
        return JSONResponse(
            status_code=410,
            content={
                "error": {
                    "message": "Realtime session has expired",
                    "type": "session_error",
                    "code": "session_expired",
                    "extra": {"expires_at": payload.expires_at, "now": now},
                }
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "session_id": payload.session_id,
            "expires_at": payload.expires_at,
            "now": now,
        },
    )


@router.get("/realtime/sessions/introspect")
async def introspect_realtime_sessions() -> JSONResponse:
    """
    Local-only introspection endpoint for realtime settings.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "realtime_model": DEFAULT_REALTIME_MODEL,
            "openai_api_base": OPENAI_API_BASE,
            "openai_realtime_beta": OPENAI_REALTIME_BETA,
            "now": time.time(),
        },
    )


def _build_ws_base() -> str:
    """
    Convert OPENAI_API_BASE (http/https) into ws/wss base for Realtime WS.
    """
    if OPENAI_API_BASE.startswith("https://"):
        return "wss://" + OPENAI_API_BASE[len("https://") :]
    if OPENAI_API_BASE.startswith("http://"):
        return "ws://" + OPENAI_API_BASE[len("http://") :]
    # Fallback: assume already ws/wss
    return OPENAI_API_BASE


@router.websocket("/realtime/ws")
async def realtime_ws(websocket: WebSocket) -> None:
    """
    WebSocket proxy between client and OpenAI Realtime WS.

    Client connects to:
      ws(s)://relay-host/v1/realtime/ws?model=...&session_id=...

    Relay connects to:
      wss://api.openai.com/v1/realtime?model=...&session_id=...
    """
    raw_subprotocols = websocket.headers.get("sec-websocket-protocol", "")
    client_subprotocols = [value.strip() for value in raw_subprotocols.split(",") if value.strip()]
    if "openai-realtime-v1" in client_subprotocols:
        await websocket.accept(subprotocol="openai-realtime-v1")
    elif "realtime" in client_subprotocols:
        await websocket.accept(subprotocol="realtime")
    else:
        await websocket.accept()

    settings = get_settings()
    if not settings.RELAY_REALTIME_WS_ENABLED:
        await websocket.close(code=1008, reason="Realtime WS is disabled on this relay")
        return

    model = (websocket.query_params.get("model") or DEFAULT_REALTIME_MODEL).strip()
    if model not in ALLOWED_REALTIME_MODELS:
        await websocket.close(code=1008, reason="Unsupported realtime model")
        return

    session_id = (websocket.query_params.get("session_id") or "").strip()
    if not session_id:
        await websocket.close(code=1008, reason="Missing session_id")
        return

    ws_base = _build_ws_base()
    query = urlencode({"model": model, "session_id": session_id})
    url = f"{ws_base}/v1/realtime?{query}"

    client_auth = websocket.headers.get("authorization")
    if client_auth:
        upstream_auth = client_auth
    elif OPENAI_API_KEY:
        upstream_auth = f"Bearer {OPENAI_API_KEY}"
    else:
        await websocket.close(code=1008, reason="Missing realtime authorization")
        return

    headers = {
        "Authorization": upstream_auth,
        "OpenAI-Beta": OPENAI_REALTIME_BETA,
    }
    upstream_subprotocols = list(dict.fromkeys(client_subprotocols + ["openai-realtime-v1", "realtime"]))

    try:
        async with ws_connect(
            url,
            extra_headers=headers,
            subprotocols=upstream_subprotocols,
        ) as upstream:
            async def client_to_upstream() -> None:
                while True:
                    message = await websocket.receive_text()
                    await upstream.send(message)

            async def upstream_to_client() -> None:
                async for message in upstream:
                    await websocket.send_text(message)

            await asyncio.gather(client_to_upstream(), upstream_to_client())
    except WebSocketDisconnect:
        return
    except ConnectionClosed:
        await websocket.close(code=1011, reason="Upstream websocket closed")
    except Exception as exc:
        logger.error(
            "Realtime WS proxy error: %s",
            {
                "exception": repr(exc),
                "openai_api_base": OPENAI_API_BASE,
                "upstream_url": url,
                "model": model,
                "session_id": session_id,
            },
        )
        await websocket.close(code=1011, reason="Realtime websocket proxy error")
```

## FILE: app/routes/register_routes.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# app/routes/register_routes.py

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter

from . import (
    actions,
    batches,
    containers,
    conversations,
    embeddings,
    files,
    health,
    images,
    models,
    proxy,
    realtime,
    responses,
    uploads,
    vector_stores,
    videos,
)


class _RouterLike(Protocol):
    """Structural protocol for FastAPI / APIRouter (anything with include_router)."""

    def include_router(self, router: APIRouter, **kwargs) -> None:  # pragma: no cover
        ...


def register_routes(app: _RouterLike) -> None:
    """Register all route families on the given FastAPI app or APIRouter.

    Ordering matters: mount specific routers first and the generic `/v1/proxy`
    last so explicit routes always win.
    """

    # Guard against double-registration (can happen in some import patterns/tests).
    if getattr(app, "_routes_registered", False):
        return
    setattr(app, "_routes_registered", True)

    # Health is special: exposes both `/health` and `/v1/health`
    app.include_router(health.router)

    # Relay diagnostics / metadata for Actions
    app.include_router(actions.router)

    # Actions wrappers (JSON-friendly routes used by ChatGPT Actions)
    app.include_router(images.actions_router)   # /v1/actions/images/*
    app.include_router(uploads.actions_router)  # /v1/actions/uploads/*
    app.include_router(videos.actions_router)   # /v1/actions/videos/*

    # Core OpenAI resource families
    app.include_router(responses.router)   # /v1/responses
    app.include_router(embeddings.router)  # /v1/embeddings
    app.include_router(images.router)      # /v1/images
    app.include_router(videos.router)      # /v1/videos
    app.include_router(models.router)      # /v1/models (local stub)

    # Files & uploads (multipart, binary content)
    app.include_router(files.router)         # /v1/files
    app.include_router(uploads.router)       # /v1/uploads
    app.include_router(vector_stores.router) # /v1/vector_stores (+ /vector_stores)

    # Higher-level surfaces
    app.include_router(conversations.router)  # /v1/conversations
    app.include_router(containers.router)     # /v1/containers
    app.include_router(batches.router)        # /v1/batches
    app.include_router(realtime.router)       # /v1/realtime (HTTP + WS)

    # Generic allowlisted proxy LAST
    app.include_router(proxy.router)          # /v1/proxy


def register_all_routes(app: _RouterLike) -> None:
    """Backwards compatibility alias (older main.py imports)."""
    register_routes(app)
```

## FILE: app/routes/responses.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.forward_openai import forward_openai_method_path, forward_openai_request
from app.core.config import get_settings

router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request):
    return await forward_openai_request(request)


class ResponsesCompactRequest(BaseModel):
    """
    Action-friendly /responses wrapper.

    - Accepts a simplified schema commonly used by ChatGPT custom actions.
    - Produces a standard Responses API call to /v1/responses.
    """

    model: Optional[str] = Field(default=None)
    input: Any = Field(...)
    instructions: Optional[str] = Field(default=None)
    max_output_tokens: Optional[int] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    top_p: Optional[float] = Field(default=None)


@router.post("/responses/compact")
async def responses_compact(payload: ResponsesCompactRequest, request: Request):
    settings = get_settings()

    req: Dict[str, Any] = {
        "model": payload.model or settings.DEFAULT_MODEL,
        "input": payload.input,
    }
    if payload.instructions is not None:
        req["instructions"] = payload.instructions
    if payload.max_output_tokens is not None:
        req["max_output_tokens"] = payload.max_output_tokens
    if payload.temperature is not None:
        req["temperature"] = payload.temperature
    if payload.top_p is not None:
        req["top_p"] = payload.top_p

    upstream_response = await forward_openai_method_path(
        "POST",
        "/v1/responses",
        json_body=req,
        inbound_headers=request.headers,
        request=request,
    )
    if upstream_response.status_code != 200:
        return upstream_response
    try:
        payload_data = json.loads(upstream_response.body.decode("utf-8"))
    except Exception:
        return upstream_response
    if isinstance(payload_data, dict):
        payload_data["object"] = "response.compaction"
    return JSONResponse(content=payload_data, status_code=upstream_response.status_code)```

## FILE: app/routes/uploads.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import base64
from typing import Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.forward_openai import build_outbound_headers, build_upstream_url, forward_openai_method_path, forward_openai_request
from app.core.http_client import get_async_httpx_client

router = APIRouter(prefix="/v1", tags=["uploads"])
actions_router = APIRouter(prefix="/v1/actions/uploads", tags=["uploads_actions"])


@router.post("/uploads")
async def create_upload(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/parts")
async def create_upload_part(upload_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/complete")
async def complete_upload(upload_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/cancel")
async def cancel_upload(upload_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.api_route(
    "/uploads/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def uploads_passthrough(path: str, request: Request) -> Response:
    upstream_path = f"/v1/uploads/{path}".rstrip("/")
    return await forward_openai_request(request, upstream_path=upstream_path)


class ActionsUploadCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose: str = Field(..., description="Upstream upload purpose")
    filename: str = Field(..., description="Original filename")
    bytes: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    expires_after: Optional[dict] = Field(default=None, description="Optional expiration settings")


class ActionsUploadPartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type")
    data_base64: str = Field(..., description="Base64-encoded bytes for part data")


class ActionsUploadCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part_ids: list[str] = Field(..., description="Ordered list of part IDs")


def _filter_response_headers(headers: httpx.Headers) -> dict:
    strip = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",
        "content-encoding",
    }
    out: dict = {}
    for k, v in headers.items():
        if k.lower() in strip:
            continue
        out[k] = v
    return out


@actions_router.post(
    "",
    operation_id="actionsUploadsCreateV1Actions",
    summary="Actions upload create (JSON)",
)
async def actions_create_upload(payload: ActionsUploadCreateRequest, request: Request) -> Response:
    return await forward_openai_method_path(
        "POST",
        "/v1/uploads",
        json_body=payload.model_dump(exclude_none=True),
        inbound_headers=request.headers,
    )


@actions_router.post(
    "/{upload_id}/parts",
    operation_id="actionsUploadsAddPartV1Actions",
    summary="Actions upload part (base64 -> multipart)",
)
async def actions_create_upload_part(upload_id: str, payload: ActionsUploadPartRequest, request: Request) -> Response:
    max_bytes = 10 * 1024 * 1024
    try:
        raw = base64.b64decode(payload.data_base64, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid data_base64: {exc}") from exc

    if not raw:
        raise HTTPException(status_code=400, detail="Empty upload part is not allowed")
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Upload part too large (>{max_bytes} bytes)")

    upstream_path = f"/v1/uploads/{upload_id}/parts"
    upstream_url = build_upstream_url(upstream_path, request=request)
    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    client = get_async_httpx_client()
    files = {"data": (payload.filename, raw, payload.mime_type)}

    try:
        resp = await client.post(upstream_url, headers=headers, files=files)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout while uploading part")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error while uploading part: {exc!r}") from exc

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
        headers=_filter_response_headers(resp.headers),
    )


@actions_router.post(
    "/{upload_id}/complete",
    operation_id="actionsUploadsCompleteV1Actions",
    summary="Actions upload complete (JSON)",
)
async def actions_complete_upload(
    upload_id: str, payload: ActionsUploadCompleteRequest, request: Request
) -> Response:
    return await forward_openai_method_path(
        "POST",
        f"/v1/uploads/{upload_id}/complete",
        json_body=payload.model_dump(exclude_none=True),
        inbound_headers=request.headers,
    )


@actions_router.post(
    "/{upload_id}/cancel",
    operation_id="actionsUploadsCancelV1Actions",
    summary="Actions upload cancel (JSON)",
)
async def actions_cancel_upload(upload_id: str, request: Request) -> Response:
    return await forward_openai_method_path(
        "POST",
        f"/v1/uploads/{upload_id}/cancel",
        json_body={},
        inbound_headers=request.headers,
    )


ActionsUploadCreateRequest.model_rebuild()
ActionsUploadPartRequest.model_rebuild()
ActionsUploadCompleteRequest.model_rebuild()```

## FILE: app/routes/vector_stores.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["vector_stores"])


async def _forward(request: Request) -> Response:
    return await forward_openai_request(request)


# ---- /v1/vector_stores (split methods to avoid duplicate operationId) ----
@router.get("/v1/vector_stores")
async def vector_stores_root_get(request: Request) -> Response:
    return await _forward(request)


@router.post("/v1/vector_stores")
async def vector_stores_root_post(request: Request) -> Response:
    return await _forward(request)


@router.put("/v1/vector_stores")
async def vector_stores_root_put(request: Request) -> Response:
    return await _forward(request)


@router.patch("/v1/vector_stores")
async def vector_stores_root_patch(request: Request) -> Response:
    return await _forward(request)


@router.delete("/v1/vector_stores")
async def vector_stores_root_delete(request: Request) -> Response:
    return await _forward(request)


# ---- /v1/vector_stores/{path:path} (split methods to avoid duplicate operationId) ----
@router.get("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_get(path: str, request: Request) -> Response:
    return await _forward(request)


@router.post("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_post(path: str, request: Request) -> Response:
    return await _forward(request)


@router.put("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_put(path: str, request: Request) -> Response:
    return await _forward(request)


@router.patch("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_patch(path: str, request: Request) -> Response:
    return await _forward(request)


@router.delete("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_delete(path: str, request: Request) -> Response:
    return await _forward(request)


# ---- Alias paths (kept hidden from OpenAPI) ----
_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@router.api_route("/vector_stores", methods=_METHODS, include_in_schema=False)
async def vector_stores_root_alias(request: Request) -> Response:
    return await _forward(request)


@router.api_route("/vector_stores/{path:path}", methods=_METHODS, include_in_schema=False)
async def vector_stores_subpaths_alias(path: str, request: Request) -> Response:
    return await _forward(request)
```

## FILE: app/routes/videos.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import base64
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.forward_openai import (
    build_outbound_headers,
    build_upstream_url,
    forward_openai_method_path,
    forward_openai_request,
)
from app.core.http_client import get_async_httpx_client
from app.models.error import ErrorResponse
from app.utils.logger import info

router = APIRouter(prefix="/v1", tags=["videos"])
actions_router = APIRouter(prefix="/v1/actions/videos", tags=["videos_actions"])

_MAX_VIDEO_BYTES = 25 * 1024 * 1024
_MAX_DURATION_SECONDS = 30
_MAX_FRAMES = 300
_ALLOWED_VIDEO_MODELS = {"sora-2", "sora-2-pro"}
_ALLOWED_VIDEO_SECONDS = {4, 8, 12}
_ALLOWED_VIDEO_SIZES = {"720x1280", "1280x720", "1024x1792", "1792x1024"}


# Canonical Videos API (per OpenAI API reference)
# - POST /v1/videos -> create a video generation job (may be multipart)
# - POST /v1/videos/{video_id}/remix -> remix an existing video
# - GET /v1/videos -> list videos
# - GET /v1/videos/{video_id} -> retrieve a video job
# - DELETE /v1/videos/{video_id} -> delete a video job
# - GET /v1/videos/{video_id}/content -> download generated content (binary)
#
# We implement main paths explicitly (clean OpenAPI + clarity),
# and keep a hidden catch-all for forward-compat endpoints.


@router.post("/videos")
async def create_video(request: Request) -> Response:
    """Create a new video generation job (JSON or multipart/form-data)."""
    info("→ [videos.create] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/videos/generations", deprecated=True)
async def create_video_legacy_generations(request: Request) -> Response:
    """
    Legacy alias: historically /v1/videos/generations in older relays.

    The current OpenAI API uses POST /v1/videos. We forward this endpoint to
    the canonical path for compatibility.
    """
    info("→ [videos.legacy_generations] %s %s", request.method, request.url.path)
    return await forward_openai_method_path(
        "POST",
        "/v1/videos",
        inbound_headers=request.headers,
        request=request,
    )


@router.post("/videos/{video_id}/remix")
async def remix_video(video_id: str, request: Request) -> Response:
    """Create a remix of an existing video job."""
    info("→ [videos.remix] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos")
async def list_videos(request: Request) -> Response:
    """List video jobs."""
    info("→ [videos.list] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}")
async def retrieve_video(video_id: str, request: Request) -> Response:
    """Retrieve a single video job."""
    info("→ [videos.retrieve] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str, request: Request) -> Response:
    """Delete a single video job."""
    info("→ [videos.delete] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}/content")
async def download_video_content(video_id: str, request: Request) -> Response:
    """Download generated content (binary) for a video job."""
    info("→ [videos.content] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "PUT", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def videos_passthrough(path: str, request: Request) -> Response:
    """Forward-compat / extra endpoints (hidden from OpenAPI schema)."""
    info("→ [videos/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


class ActionsVideoGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: Optional[str] = Field(default=None, description="Text prompt for video generation")
    model: Optional[str] = Field(default=None, description="Model name")
    size: Optional[str] = Field(default=None, description="Output size (e.g., 720x1280)")
    seconds: Optional[int] = Field(default=None, description="Clip duration in seconds")
    duration_seconds: Optional[int] = Field(default=None, description="Duration in seconds (legacy)")
    frames: Optional[int] = Field(default=None, description="Frame count (legacy)")
    data_base64: Optional[str] = Field(default=None, description="Optional base64-encoded input video")
    input_reference_base64: Optional[str] = Field(
        default=None,
        description="Optional base64-encoded input reference (alias for data_base64)",
    )
    filename: Optional[str] = Field(default="input.mp4", description="Input filename")
    mime_type: Optional[str] = Field(default="video/mp4", description="Input MIME type")


def _filter_response_headers(headers: httpx.Headers) -> dict:
    strip = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",
        "content-encoding",
    }
    out: dict = {}
    for k, v in headers.items():
        if k.lower() in strip:
            continue
        out[k] = v
    return out


def _error_response(
    message: str,
    *,
    status_code: int = 400,
    param: Optional[str] = None,
    code: Optional[str] = None,
) -> Response:
    return ErrorResponse.from_message(
        message,
        param=param,
        code=code,
    ).to_response(status_code=status_code)


@actions_router.post(
    "",
    operation_id="actionsVideosCreateV1Actions",
    summary="Actions wrapper for /v1/videos",
)
async def actions_create_video(request: Request) -> Response:
    info("→ [actions.videos.create] %s %s", request.method, request.url.path)
    return await forward_openai_request(request, upstream_path="/v1/videos")


@actions_router.post(
    "/{video_id}/remix",
    operation_id="actionsVideosRemixV1Actions",
    summary="Actions wrapper for /v1/videos/{video_id}/remix",
)
async def actions_remix_video(video_id: str, request: Request) -> Response:
    info("→ [actions.videos.remix] %s %s", request.method, request.url.path)
    return await forward_openai_request(request, upstream_path=f"/v1/videos/{video_id}/remix")


@actions_router.post(
    "/generations",
    operation_id="actionsVideosGenerationsV1Actions",
    summary="Actions wrapper for /v1/videos/generations (multipart)",
)
async def actions_generate_video(payload: ActionsVideoGenerationRequest, request: Request) -> Response:
    if not payload.prompt:
        return _error_response(
            "prompt is required",
            param="prompt",
        )

    if payload.model is not None and payload.model not in _ALLOWED_VIDEO_MODELS:
        return _error_response(
            f"model must be one of: {', '.join(sorted(_ALLOWED_VIDEO_MODELS))}",
            param="model",
        )

    if payload.size is not None and payload.size not in _ALLOWED_VIDEO_SIZES:
        return _error_response(
            f"size must be one of: {', '.join(sorted(_ALLOWED_VIDEO_SIZES))}",
            param="size",
        )

    seconds_value = payload.seconds if payload.seconds is not None else payload.duration_seconds
    if seconds_value is not None and seconds_value not in _ALLOWED_VIDEO_SECONDS:
        return _error_response(
            f"seconds must be one of: {', '.join(str(s) for s in sorted(_ALLOWED_VIDEO_SECONDS))}",
            param="seconds",
        )

    if payload.duration_seconds is not None and payload.duration_seconds > _MAX_DURATION_SECONDS:
        return _error_response(
            f"duration_seconds exceeds {_MAX_DURATION_SECONDS}",
            param="duration_seconds",
        )
    if payload.frames is not None and payload.frames > _MAX_FRAMES:
        return _error_response(
            f"frames exceeds {_MAX_FRAMES}",
            param="frames",
        )

    raw: bytes | None = None
    base64_source = payload.data_base64 if payload.data_base64 is not None else payload.input_reference_base64
    if base64_source is not None:
        try:
            raw = base64.b64decode(base64_source, validate=True)
        except Exception as exc:
            return _error_response(
                f"Invalid data_base64: {exc}",
                param="data_base64",
            )

    if raw is not None:
        if len(raw) == 0:
            return _error_response(
                "Empty input video is not allowed",
                param="data_base64",
            )
        if len(raw) > _MAX_VIDEO_BYTES:
            return _error_response(
                f"Input video too large (>{_MAX_VIDEO_BYTES} bytes)",
                status_code=413,
                param="data_base64",
                code="input_too_large",
            )

    upstream_path = "/v1/videos/generations"
    upstream_url = build_upstream_url(upstream_path, request=request)
    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    data: dict[str, str] = {}
    if payload.prompt:
        data["prompt"] = payload.prompt
    if payload.model:
        data["model"] = payload.model
    if payload.size:
        data["size"] = payload.size
    if payload.duration_seconds is not None:
        data["duration_seconds"] = str(payload.duration_seconds)
    if payload.seconds is not None:
        data["seconds"] = str(payload.seconds)
    if payload.frames is not None:
        data["frames"] = str(payload.frames)

    files = None
    if raw is not None:
        files = {
            "file": (payload.filename or "input.mp4", raw, payload.mime_type or "video/mp4"),
        }

    client = get_async_httpx_client()
    try:
        resp = await client.post(upstream_url, headers=headers, data=data, files=files)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout while generating video")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error while generating video: {exc!r}") from exc

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
        headers=_filter_response_headers(resp.headers),
    )


ActionsVideoGenerationRequest.model_rebuild()
```

## FILE: app/utils/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
```

## FILE: app/utils/authy.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import hmac

from fastapi import HTTPException

from app.core.config import settings


def _get_expected_key() -> str:
    """
    Prefer settings.RELAY_KEY, but keep a fallback to RELAY_AUTH_TOKEN.
    """
    if getattr(settings, "RELAY_KEY", None):
        return str(settings.RELAY_KEY)
    token = getattr(settings, "RELAY_AUTH_TOKEN", None)
    return str(token or "")


def check_relay_key(*, authorization: str | None, x_relay_key: str | None) -> None:
    """
    Validate the inbound request key against settings.RELAY_KEY.

    Accepted locations:
      - X-Relay-Key: <token>
      - Authorization: Bearer <token>

    Behavior:
      - If RELAY_AUTH_ENABLED is false, this is a no-op.
      - If enabled and no key is configured, raise 500 (misconfiguration).
      - If missing token, raise 401 "Missing relay key".
      - If token is invalid, raise 401 "Invalid relay key".
      - If Authorization is present but not Bearer, raise 401 mentioning Bearer.
    """
    if not getattr(settings, "RELAY_AUTH_ENABLED", False):
        return

    expected = _get_expected_key().encode("utf-8")
    if not expected:
        raise HTTPException(
            status_code=500,
            detail="Relay auth misconfigured: RELAY_KEY is empty when auth is enabled",
        )

    presented: list[str] = []
    if x_relay_key:
        presented.append(x_relay_key)

    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            presented.append(parts[1])
        else:
            raise HTTPException(
                status_code=401,
                detail="Authorization header must use Bearer scheme",
            )

    if not presented:
        raise HTTPException(status_code=401, detail="Missing relay key")

    for token in presented:
        if hmac.compare_digest(token.encode("utf-8"), expected):
            return

    raise HTTPException(status_code=401, detail="Invalid relay key")
```

## FILE: app/utils/error_handler.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# app/utils/error_handler.py

from __future__ import annotations

from typing import Any, Optional, Type

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from openai._exceptions import OpenAIError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import ClientDisconnect

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Non-standard but widely used by proxies (e.g., nginx) to signal "Client Closed Request".
CLIENT_CLOSED_REQUEST_STATUS = 499


def _base_error_payload(
    message: str,
    status: int,
    code: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "error": {
            "message": message,
            "type": "relay_error",
            "param": None,
            "code": code,
        },
        "status": status,
    }


# ExceptionGroup exists in Python 3.11+
try:
    ExceptionGroupType: Optional[Type[BaseException]] = ExceptionGroup  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    ExceptionGroupType = None


def _is_client_disconnect(exc: BaseException) -> bool:
    """
    Return True if:
      - exc is ClientDisconnect, OR
      - exc is an ExceptionGroup where *every* inner exception is a ClientDisconnect.
    """
    if isinstance(exc, ClientDisconnect):
        return True

    if ExceptionGroupType is not None and isinstance(exc, ExceptionGroupType):
        try:
            # ExceptionGroup exposes `.exceptions` (tuple of underlying exceptions)
            inner = exc.exceptions  # type: ignore[attr-defined]
            return all(_is_client_disconnect(e) for e in inner)
        except Exception:
            return False

    return False


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning("HTTP error", extra={"status_code": exc.status_code, "detail": exc.detail})
        return JSONResponse(
            status_code=exc.status_code,
            content=_base_error_payload(str(exc.detail), exc.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error", extra={"errors": exc.errors()})
        return JSONResponse(
            status_code=422,
            content=_base_error_payload("Validation error", 422),
        )

    @app.exception_handler(OpenAIError)
    async def openai_exception_handler(request: Request, exc: OpenAIError):
        logger.error("OpenAI API error", extra={"error": str(exc)})
        return JSONResponse(
            status_code=502,
            content=_base_error_payload(f"Upstream OpenAI error: {exc}", 502),
        )

    @app.exception_handler(ClientDisconnect)
    async def client_disconnect_handler(request: Request, exc: ClientDisconnect):
        # Client closed connection mid-request. This is not a server bug; do not log as ERROR.
        logger.info(
            "Client disconnected",
            extra={"method": request.method, "path": request.url.path},
        )
        return JSONResponse(
            status_code=CLIENT_CLOSED_REQUEST_STATUS,
            content=_base_error_payload("Client disconnected", CLIENT_CLOSED_REQUEST_STATUS),
        )

    if ExceptionGroupType is not None:

        @app.exception_handler(ExceptionGroupType)  # type: ignore[arg-type]
        async def exception_group_handler(request: Request, exc: BaseException):
            # Starlette/AnyIO may wrap disconnects inside an ExceptionGroup.
            if _is_client_disconnect(exc):
                logger.info(
                    "Client disconnected (exception group)",
                    extra={"method": request.method, "path": request.url.path},
                )
                return JSONResponse(
                    status_code=CLIENT_CLOSED_REQUEST_STATUS,
                    content=_base_error_payload("Client disconnected", CLIENT_CLOSED_REQUEST_STATUS),
                )

            logger.exception("Unhandled exception group")
            return JSONResponse(
                status_code=500,
                content=_base_error_payload("Internal Server Error", 500),
            )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Defensive fallback: in case a disconnect slips through as a generic Exception.
        if _is_client_disconnect(exc):
            logger.info(
                "Client disconnected (caught by generic handler)",
                extra={"method": request.method, "path": request.url.path},
            )
            return JSONResponse(
                status_code=CLIENT_CLOSED_REQUEST_STATUS,
                content=_base_error_payload("Client disconnected", CLIENT_CLOSED_REQUEST_STATUS),
            )

        logger.exception("Unhandled server error")
        return JSONResponse(
            status_code=500,
            content=_base_error_payload("Internal Server Error", 500),
        )
```

## FILE: app/utils/http_client.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

from app.core.http_client import get_async_httpx_client

__all__ = ["get_async_httpx_client"]
```

## FILE: app/utils/logger.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional
from logging.handlers import RotatingFileHandler

_LOGGER_ROOT_NAME = "chatgpt_team_relay"


def _coerce_log_level(value: Any) -> int:
    """
    Convert arbitrary env/config values into a valid logging level integer.

    Why:
      - Render env vars are always strings; misconfig like LOG_LEVEL=FALSE
        will crash logging.setLevel("FALSE") with ValueError.
      - We harden to avoid taking the whole service down due to config typos.

    Accepts:
      - int levels (e.g. 20)
      - standard names (DEBUG/INFO/WARNING/ERROR/CRITICAL)
      - common aliases (WARN, FATAL)
      - "true/false" -> fallback to INFO
    """
    if isinstance(value, int) and not isinstance(value, bool):
        return value

    if isinstance(value, bool):
        # Treat booleans as "use default verbosity" rather than crashing.
        return logging.INFO

    s = str(value or "").strip()
    if not s:
        return logging.INFO

    s_upper = s.upper()

    # Common misconfigs where someone thought this was a boolean toggle.
    if s_upper in {"TRUE", "FALSE"}:
        return logging.INFO

    # Numeric strings
    if s_upper.isdigit():
        try:
            return int(s_upper)
        except Exception:
            return logging.INFO

    # Common aliases
    if s_upper == "WARN":
        s_upper = "WARNING"
    elif s_upper == "FATAL":
        s_upper = "CRITICAL"

    # Official mapping (Py 3.11+)
    mapping = logging.getLevelNamesMapping()
    if s_upper in mapping:
        return int(mapping[s_upper])

    return logging.INFO


def configure_logging(level: Optional[str] = None) -> None:
    """Idempotent logging setup for local dev and production.

    - Uses a single StreamHandler to stdout
    - Avoids duplicate handlers on reload
    - Sets a clean, grep-friendly format
    """
    resolved_level = _coerce_log_level(level or os.getenv("LOG_LEVEL") or "INFO")

    root_logger = logging.getLogger(_LOGGER_ROOT_NAME)

    # Idempotency: don't stack handlers on reload.
    if getattr(root_logger, "_relay_configured", False):
        root_logger.setLevel(resolved_level)
        for h in list(root_logger.handlers):
            h.setLevel(resolved_level)
        return

    root_logger.setLevel(resolved_level)
    root_logger.propagate = False

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(resolved_level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger.addHandler(handler)

    error_log_path = os.getenv("ERROR_LOG_PATH", "data/logs/errors.log").strip()
    if error_log_path:
        error_log_dir = os.path.dirname(error_log_path)
        if error_log_dir:
            os.makedirs(error_log_dir, exist_ok=True)
        try:
            with open(error_log_path, "a", encoding="utf-8"):
                pass
        except OSError:
            error_log_path = ""

    if error_log_path:
        error_handler = RotatingFileHandler(
            error_log_path,
            maxBytes=int(os.getenv("ERROR_LOG_MAX_BYTES", str(5 * 1024 * 1024))),
            backupCount=int(os.getenv("ERROR_LOG_BACKUP_COUNT", "5")),
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root_logger.addHandler(error_handler)

    setattr(root_logger, "_relay_configured", True)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the relay root."""
    if not name:
        return logging.getLogger(_LOGGER_ROOT_NAME)
    return logging.getLogger(f"{_LOGGER_ROOT_NAME}.{name}")


# Default logger used across the codebase.
relay_log = get_logger("relay")


# ---------------------------------------------------------------------------
# Backward-compatible convenience functions.
# Some older route modules imported these directly (e.g., `from app.utils.logger import info`).
# ---------------------------------------------------------------------------

def debug(msg: str, *args, **kwargs) -> None:
    relay_log.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    relay_log.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    relay_log.warning(msg, *args, **kwargs)


# Common alias
warn = warning


def error(msg: str, *args, **kwargs) -> None:
    relay_log.error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs) -> None:
    relay_log.exception(msg, *args, **kwargs)
```

## BASELINE (tests/)

## FILE: tests/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
```

## FILE: tests/client.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# tests/client.py

import os
from starlette.testclient import TestClient

# Ensure the app sees a test-friendly environment *before* it is imported.
os.environ.setdefault("APP_MODE", "test")
os.environ.setdefault("ENVIRONMENT", "test")

# You explicitly chose Option A: disable relay auth in tests.
# This makes RelayAuthMiddleware's check_relay_key() a no-op.
os.environ.setdefault("RELAY_AUTH_ENABLED", "false")

# Upstream base URL can stay default; override if you proxy:
os.environ.setdefault("OPENAI_API_BASE", "https://api.openai.com/v1")

from app.main import app  # noqa: E402  (import after env is set)


def _build_client() -> TestClient:
    client = TestClient(app)

    # Optional: if you ever want to test auth-enabled paths locally,
    # set RELAY_KEY in your environment and this will send an Authorization header.
    relay_key = os.getenv("RELAY_KEY")
    if relay_key:
        client.headers.update({"Authorization": f"Bearer {relay_key}"})

    return client


# Shared client instance used by all tests via the fixture in conftest.py
client: TestClient = _build_client()
```

## FILE: tests/conftest.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import os
from typing import Any, AsyncIterator, Dict, Optional

import httpx
import pytest
import pytest_asyncio

from app.main import app as fastapi_app


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v not in (None, "") else default


def _relay_base_url() -> str:
    return (_env("RELAY_BASE_URL", "http://localhost:8000") or "http://localhost:8000").rstrip("/")


def _relay_token() -> Optional[str]:
    # Prefer RELAY_TOKEN; fall back to RELAY_KEY for convenience.
    return _env("RELAY_TOKEN") or _env("RELAY_KEY")


def _auth_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Produce relay auth headers.

    We always send Authorization: Bearer <token> when a token is present.
    If RELAY_AUTH_HEADER is configured (e.g., x-relay-key), we ALSO send that header
    with the raw token value, to stay compatible with both auth styles.
    """
    headers: Dict[str, str] = {}
    token = _relay_token()

    if token:
        headers["Authorization"] = f"Bearer {token}"
        configured = _env("RELAY_AUTH_HEADER")
        if configured and configured.lower() not in ("authorization",):
            headers[configured] = token

    if extra:
        headers.update(extra)
    return headers


async def _probe_relay_or_skip(client: httpx.AsyncClient) -> None:
    """
    Make failures actionable:
      - Skip if relay is unreachable (forgot to start uvicorn, wrong base URL)
      - Skip if obviously missing token for Render (placeholder/dummy)
      - Otherwise continue and let tests assert behavior
    """
    base_url = _relay_base_url()
    token = _relay_token()

    # Common footgun: running against Render with RELAY_TOKEN unset or dummy
    if "onrender.com" in base_url and (not token or token.strip().lower() == "dummy"):
        pytest.skip(
            "RELAY_TOKEN is missing/placeholder while targeting Render. "
            "Export a real RELAY_TOKEN (and optionally RELAY_KEY) before running integration tests."
        )

    # Reachability probe (no hard dependency on auth-protected endpoints).
    try:
        r = await client.get("/v1/actions/ping")
    except Exception as e:
        pytest.skip(
            f"Relay not reachable at {base_url}. Start uvicorn locally or fix RELAY_BASE_URL. "
            f"Probe error: {type(e).__name__}: {e}"
        )

    # If ping itself is failing badly, skip.
    if r.status_code >= 500:
        pytest.skip(f"Relay is returning {r.status_code} for /v1/actions/ping; skipping integration tests.")


@pytest_asyncio.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """
    Live HTTP client for integration tests.

    These integration tests are intended to hit a running relay (localhost or Render),
    so they exercise the real middleware stack + upstream forwarding.
    """
    base_url = _relay_base_url()

    timeout = httpx.Timeout(
        connect=float(_env("HTTPX_CONNECT_TIMEOUT_S", "10")),
        read=float(_env("HTTPX_READ_TIMEOUT_S", "60")),
        write=float(_env("HTTPX_WRITE_TIMEOUT_S", "60")),
        pool=float(_env("HTTPX_POOL_TIMEOUT_S", "10")),
    )

    async with httpx.AsyncClient(
        base_url=base_url,
        headers=_auth_headers(),
        timeout=timeout,
        follow_redirects=True,
    ) as c:
        await _probe_relay_or_skip(c)
        yield c


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    """
    In-process ASGI client for local E2E tests.

    This does NOT require a running uvicorn server; it calls the FastAPI app directly.
    We still attach relay auth headers by default so /v1/* endpoints work when auth is enabled.
    """
    timeout = httpx.Timeout(
        connect=float(_env("HTTPX_CONNECT_TIMEOUT_S", "10")),
        read=float(_env("HTTPX_READ_TIMEOUT_S", "60")),
        write=float(_env("HTTPX_WRITE_TIMEOUT_S", "60")),
        pool=float(_env("HTTPX_POOL_TIMEOUT_S", "10")),
    )

    transport = httpx.ASGITransport(app=fastapi_app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers=_auth_headers(),
        timeout=timeout,
        follow_redirects=True,
    ) as c:
        yield c
```

## FILE: tests/relay_client_example.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# relay_client_example.py
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional

import requests


def _env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def _headers(relay_key: str) -> Dict[str, str]:
    # Your relay supports either X-Relay-Key or Authorization.
    # Choose ONE and keep it consistent with your OpenAPI / GPT Action auth scheme.
    return {
        "X-Relay-Key": relay_key,
        "Content-Type": "application/json",
    }


def get_manifest(base_url: str, relay_key: str) -> Dict[str, Any]:
    r = requests.get(f"{base_url}/manifest", headers=_headers(relay_key), timeout=30)
    r.raise_for_status()
    return r.json()


def create_response(base_url: str, relay_key: str, model: str, user_input: str) -> Dict[str, Any]:
    payload = {
        "model": model,
        "input": user_input,
        "stream": False,  # Actions-safe. SSE streaming is for non-Actions clients.
    }
    r = requests.post(
        f"{base_url}/v1/responses",
        headers=_headers(relay_key),
        data=json.dumps(payload),
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


def main() -> int:
    base_url = _env("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
    relay_key = _env("RELAY_KEY", "dummy")
    model = os.getenv("RELAY_MODEL", "gpt-5.1")

    manifest = get_manifest(base_url, relay_key)
    print("=== /manifest (truncated) ===")
    # Print just the top-level keys to avoid huge output
    print("keys:", list(manifest.keys()))

    resp = create_response(base_url, relay_key, model, "Say hi in one sentence.")
    print("\n=== /v1/responses ===")
    print(json.dumps(resp, indent=2)[:4000])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
```

## FILE: tests/test_extended_routes_smoke_integration.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
"""Extended route smoke tests (integration).

These tests intentionally focus on *wiring* and *non-5xx* behavior for
route families that are not covered by the success gates.

They are safe to run against:
  - Local relay: http://localhost:8000 (default)
  - Remote relay: set RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com

Many routes proxy to OpenAI. To avoid false failures on machines where the
relay is not configured with an upstream key, tests that may call OpenAI are
skipped unless INTEGRATION_OPENAI_API_KEY=1.
"""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, Iterable

import pytest
import requests


RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")

# NOTE: The server uses RELAY_KEY, but existing integration tests sometimes use RELAY_TOKEN.
# We accept either to reduce operator friction.
RELAY_TOKEN = (
    os.getenv("RELAY_TOKEN")
    or os.getenv("RELAY_KEY")
    or os.getenv("RELAY_AUTH_TOKEN")
    or "dummy"
)

DEFAULT_TIMEOUT_S = float(os.getenv("RELAY_TEST_TIMEOUT_S", "30"))
INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"

# Minimal valid 1x1 PNG (transparent-ish). Avoids adding binary fixtures to the repo.
_PNG_1X1_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
_PNG_1X1_BYTES = base64.b64decode(_PNG_1X1_B64)


def _auth_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    headers = {"Authorization": f"Bearer {RELAY_TOKEN}"}
    if extra:
        headers.update(extra)
    return headers


def _skip_if_no_real_key() -> None:
    """Skip tests that may call upstream OpenAI unless explicitly enabled."""
    if os.getenv(INTEGRATION_ENV_VAR, "").strip() != "1":
        pytest.skip(f"Set {INTEGRATION_ENV_VAR}=1 to run upstream-proxy smoke tests")


def _get_openapi() -> Dict[str, Any]:
    r = requests.get(
        f"{RELAY_BASE_URL}/openapi.json",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code == 200, f"openapi.json returned {r.status_code}: {r.text[:400]}"
    return r.json()


def _path_exists(openapi: Dict[str, Any], path: str) -> bool:
    return path in (openapi.get("paths") or {})


def _pick_first_existing(openapi: Dict[str, Any], candidates: Iterable[str]) -> str:
    for p in candidates:
        if _path_exists(openapi, p):
            return p
    raise AssertionError(f"None of the candidate paths exist in openapi: {list(candidates)}")


@pytest.mark.integration
def test_openapi_includes_extended_route_families() -> None:
    """Validate route registration (schema), independent of upstream."""

    spec = _get_openapi()
    paths = spec.get("paths") or {}
    assert isinstance(paths, dict) and paths, "openapi.json has no paths"

    # Actions
    assert (
        "/v1/actions/ping" in paths or "/actions/ping" in paths
    ), "Missing actions ping route"
    assert (
        "/v1/actions/relay_info" in paths or "/actions/relay_info" in paths
    ), "Missing actions relay_info route"

    # Proxy
    assert "/v1/proxy" in paths, "Missing /v1/proxy route"

    # Images
    assert "/v1/images/generations" in paths, "Missing /v1/images/generations route"
    assert "/v1/images/variations" in paths, "Missing /v1/images/variations route"

    # Vector stores
    assert "/v1/vector_stores" in paths, "Missing /v1/vector_stores route"

    # Conversations
    assert "/v1/conversations" in paths, "Missing /v1/conversations route"

    # Realtime sessions (REST). WebSocket path may not appear in schema.
    assert "/v1/realtime/sessions" in paths, "Missing /v1/realtime/sessions route"


@pytest.mark.integration
def test_actions_ping_and_relay_info_smoke() -> None:
    """Actions endpoints should be purely local and return JSON."""

    spec = _get_openapi()

    ping_path = _pick_first_existing(spec, ["/v1/actions/ping", "/actions/ping"])
    r = requests.get(
        f"{RELAY_BASE_URL}{ping_path}",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code == 200, f"{ping_path} returned {r.status_code}: {r.text[:400]}"
    assert "application/json" in (r.headers.get("Content-Type") or "")
    body = r.json()
    assert isinstance(body, dict)

    info_path = _pick_first_existing(spec, ["/v1/actions/relay_info", "/actions/relay_info"])
    r = requests.get(
        f"{RELAY_BASE_URL}{info_path}",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code == 200, f"{info_path} returned {r.status_code}: {r.text[:400]}"
    assert "application/json" in (r.headers.get("Content-Type") or "")
    body = r.json()
    assert isinstance(body, dict)


@pytest.mark.integration
def test_proxy_blocklist_smoke() -> None:
    """Proxy should block high-risk endpoints locally (no upstream required)."""

    payload = {"method": "GET", "path": "/v1/evals"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/proxy",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    # Either 403 from relay (preferred) or 404 if upstream ever changes; must not be 5xx.
    assert r.status_code < 500, f"proxy blocklist returned {r.status_code}: {r.text[:400]}"
    assert r.status_code in (403, 404), f"Unexpected proxy blocklist status: {r.status_code}"


@pytest.mark.integration
def test_proxy_allowlist_models_smoke() -> None:
    """Proxy allowlist should permit /v1/models and return JSON from upstream."""

    _skip_if_no_real_key()

    payload = {"method": "GET", "path": "/v1/models"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/proxy",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"proxy /v1/models returned {r.status_code}: {r.text[:400]}"
    # Upstream should return JSON list.
    assert "application/json" in (r.headers.get("Content-Type") or "")
    body = r.json()
    assert isinstance(body, dict)
    assert body.get("object") == "list", f"Unexpected /v1/models object: {body.get('object')}"


@pytest.mark.integration
def test_images_generations_wiring_no_5xx() -> None:
    """Images generations endpoint should never produce a relay 5xx due to wiring."""

    _skip_if_no_real_key()

    # Use an intentionally invalid model to avoid any billable work; wiring is the goal.
    payload = {"model": "__invalid_model__", "prompt": "ping"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/images/generations",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"images generations returned {r.status_code}: {r.text[:400]}"


@pytest.mark.integration
def test_images_variations_wiring_no_5xx() -> None:
    """Images variations endpoint should never produce a relay 5xx due to wiring."""

    _skip_if_no_real_key()

    # Multipart/form-data: file + fields.
    # Use an intentionally invalid model to avoid any billable work; wiring is the goal.
    files = {"image": ("input.png", _PNG_1X1_BYTES, "image/png")}
    data = {"model": "__invalid_model__", "n": "1", "size": "256x256"}

    r = requests.post(
        f"{RELAY_BASE_URL}/v1/images/variations",
        headers=_auth_headers(),
        files=files,
        data=data,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"images variations returned {r.status_code}: {r.text[:400]}"


@pytest.mark.integration
def test_vector_stores_list_no_5xx() -> None:
    """Vector stores list should route and never 5xx due to relay wiring."""

    _skip_if_no_real_key()

    r = requests.get(
        f"{RELAY_BASE_URL}/v1/vector_stores?limit=1",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"vector_stores list returned {r.status_code}: {r.text[:400]}"


@pytest.mark.integration
def test_conversations_list_no_5xx() -> None:
    """Conversations list should route and never 5xx due to relay wiring."""

    _skip_if_no_real_key()

    r = requests.get(
        f"{RELAY_BASE_URL}/v1/conversations?limit=1",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"conversations list returned {r.status_code}: {r.text[:400]}"


@pytest.mark.integration
def test_realtime_sessions_create_no_5xx() -> None:
    """Realtime sessions should route; we only gate on non-5xx."""

    _skip_if_no_real_key()

    payload = {"model": "gpt-4.1-mini"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/realtime/sessions",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"realtime sessions returned {r.status_code}: {r.text[:400]}"
```

## FILE: tests/test_files_and_batches_integration.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
"""
tests/test_files_and_batches_integration.py

Integration tests for the relay's Files + Batches behavior.

These tests are intentionally "black box": they talk to a *running* relay instance
over HTTP (local uvicorn on :8000, or a deployed URL).

Environment
-----------
RELAY_BASE_URL
  Base URL for the relay. Defaults to http://localhost:8000

RELAY_TOKEN / RELAY_KEY
  Relay auth token. Tests prefer RELAY_TOKEN, and fall back to RELAY_KEY.

INTEGRATION_OPENAI_API_KEY
  Gate for upstream-hitting tests. If unset/empty, OpenAI-dependent tests
  are skipped (to keep default CI runs cheap/safe).
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, AsyncIterator, Dict

import httpx
import pytest
import pytest_asyncio

RELAY_BASE_URL = (os.getenv("RELAY_BASE_URL") or "http://localhost:8000").rstrip("/")
RELAY_TOKEN = os.getenv("RELAY_TOKEN") or os.getenv("RELAY_KEY") or "dummy"

INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


DEFAULT_TIMEOUT_S = _env_float("RELAY_TEST_TIMEOUT_S", 60.0)


def _has_openai_key() -> bool:
    raw = (os.getenv(INTEGRATION_ENV_VAR) or "").strip().lower()
    return raw in {"1", "true", "yes"}


def _auth_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    """
    Send both headers so tests work across relay deployments that check either:
      - Authorization: Bearer <token>
      - X-Relay-Key: <token>
    """
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {RELAY_TOKEN}",
        "X-Relay-Key": RELAY_TOKEN,
    }
    if extra:
        headers.update(extra)
    return headers


async def _request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    retries: int = 2,
    retry_sleep_s: float = 0.5,
    **kwargs: Any,
) -> httpx.Response:
    last_exc: Exception | None = None
    last_resp: httpx.Response | None = None

    for attempt in range(retries + 1):
        try:
            resp = await client.request(method, url, **kwargs)
            last_resp = resp
            # For tests: return any non-5xx response so assertions can inspect it.
            if resp.status_code < 500:
                return resp
        except httpx.HTTPError as exc:
            last_exc = exc

        if attempt < retries:
            await asyncio.sleep(retry_sleep_s)

    if last_resp is not None:
        return last_resp
    assert last_exc is not None
    raise last_exc


@pytest_asyncio.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """
    IMPORTANT FIX:
    In `asyncio_mode=strict`, async fixtures must use `@pytest_asyncio.fixture`.
    Otherwise pytest passes an async generator object through to tests and you get:
      AttributeError: 'async_generator' object has no attribute 'request'
    """
    async with httpx.AsyncClient(
        base_url=RELAY_BASE_URL,
        timeout=DEFAULT_TIMEOUT_S,
        headers=_auth_headers(),
        follow_redirects=True,
    ) as c:
        yield c


@pytest.mark.integration
@pytest.mark.asyncio
async def test_proxy_blocks_evals_and_fine_tune(client: httpx.AsyncClient) -> None:
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    # Evals blocked
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={"method": "GET", "path": "/v1/evals"},
    )
    assert r.status_code in (403, 404), f"Unexpected evals proxy status: {r.status_code} {r.text[:200]}"

    # Fine-tune blocked
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={"method": "GET", "path": "/v1/fine_tuning/jobs"},
    )
    assert r.status_code in (403, 404), f"Unexpected fine-tune proxy status: {r.status_code} {r.text[:200]}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_proxy_allowlist_files_meta_and_vector_stores_root_write(client: httpx.AsyncClient) -> None:
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    file_id = "file-does-not-exist"
    for method in ("GET", "DELETE"):
        r = await _request_with_retry(
            client,
            "POST",
            "/v1/proxy",
            headers=_auth_headers({"Content-Type": "application/json"}),
            json={"method": method, "path": f"/v1/files/{file_id}"},
        )
        assert r.status_code < 500, f"proxy files metadata {method} returned {r.status_code}: {r.text[:200]}"
        assert r.status_code != 403, f"proxy files metadata {method} blocked: {r.text[:200]}"

    for method in ("PUT", "PATCH", "DELETE"):
        payload: Dict[str, Any] = {"method": method, "path": "/v1/vector_stores"}
        if method in {"PUT", "PATCH"}:
            payload["body"] = {}
        r = await _request_with_retry(
            client,
            "POST",
            "/v1/proxy",
            headers=_auth_headers({"Content-Type": "application/json"}),
            json=payload,
        )
        assert r.status_code < 500, f"proxy vector_stores {method} returned {r.status_code}: {r.text[:200]}"
        assert r.status_code != 403, f"proxy vector_stores {method} blocked: {r.text[:200]}"

    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={"method": "GET", "path": f"/v1/files/{file_id}/content"},
    )
    assert r.status_code == 403, f"proxy files content should be blocked: {r.status_code} {r.text[:200]}"

    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={"method": "POST", "path": "/v1/uploads"},
    )
    assert r.status_code == 403, f"proxy uploads should be blocked: {r.status_code} {r.text[:200]}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_data_file_download_is_forbidden(client: httpx.AsyncClient) -> None:
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    data = {"purpose": "user_data"}
    files = {"file": ("relay_ping.txt", b"ping", "text/plain")}

    r = await _request_with_retry(
        client,
        "POST",
        "/v1/files",
        headers=_auth_headers(),
        data=data,
        files=files,
    )
    assert r.status_code < 500, f"file upload returned {r.status_code}: {r.text[:400]}"
    body = r.json()
    file_id = body.get("id")
    assert isinstance(file_id, str) and file_id, f"unexpected file id: {body}"

    # user_data file downloads should be blocked by the relay privacy guardrail.
    #
    # Observed behavior: the relay returns an OpenAI-shaped error payload with HTTP 400
    # (invalid_request_error) and message like:
    #   "Not allowed to download files of purpose: user_data"
    #
    # Some deployments may choose to map this to 403. Either is acceptable as long as
    # the guardrail is clearly enforced and never 2xx.
    r = await _request_with_retry(client, "GET", f"/v1/files/{file_id}/content", headers=_auth_headers())
    assert r.status_code in (400, 403), f"expected blocked download, got {r.status_code}: {r.text[:200]}"

    if r.status_code == 400:
        # Validate the error is specifically about user_data download being blocked.
        try:
            err_body = r.json()
        except Exception:
            pytest.fail(f"expected JSON error body for 400, got non-JSON: {r.text[:200]}")

        msg = (
            ((err_body.get("error") or {}).get("message") or "")
            if isinstance(err_body, dict)
            else ""
        ).lower()
        assert "user_data" in msg and "not allowed" in msg, f"unexpected 400 error message: {msg!r}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_batch_output_file_is_downloadable(client: httpx.AsyncClient) -> None:
    """
    Batch completion latency is not deterministic. The relay is correct if:
      - batch can be created
      - status progresses (validating/in_progress/finalizing)
      - once completed, output_file_id content downloads successfully

    If the batch does not complete within the configured timeout, skip rather than fail.
    """
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    batch_timeout_s = _env_float("BATCH_TIMEOUT_SECONDS", 600.0)
    poll_interval_s = _env_float("BATCH_POLL_INTERVAL_SECONDS", 2.0)

    jsonl_line = (
        json.dumps(
            {
                "custom_id": "ping-1",
                "method": "POST",
                "url": "/v1/responses",
                "body": {"model": "gpt-5.1", "input": "Return exactly: pong"},
            }
        ).encode("utf-8")
        + b"\n"
    )

    # Upload batch input
    data = {"purpose": "batch"}
    files = {"file": ("batch_input.jsonl", jsonl_line, "application/jsonl")}
    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_headers(), data=data, files=files)
    assert r.status_code < 500, f"batch input upload returned {r.status_code}: {r.text[:400]}"
    file_id = r.json().get("id")
    assert isinstance(file_id, str) and file_id, f"unexpected batch input file id: {r.text[:200]}"

    # Create batch
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/batches",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={
            "input_file_id": file_id,
            "endpoint": "/v1/responses",
            "completion_window": "24h",
        },
    )
    assert r.status_code < 500, f"batch create returned {r.status_code}: {r.text[:400]}"
    batch = r.json()
    batch_id = batch.get("id")
    assert isinstance(batch_id, str) and batch_id, f"unexpected batch id: {batch}"

    # Poll status
    loop = asyncio.get_running_loop()
    deadline = loop.time() + batch_timeout_s

    output_file_id: str | None = None
    status: str | None = None

    while loop.time() < deadline:
        r = await _request_with_retry(client, "GET", f"/v1/batches/{batch_id}", headers=_auth_headers())
        assert r.status_code < 500, f"batch retrieve returned {r.status_code}: {r.text[:200]}"

        body = r.json()
        status = body.get("status")
        output_file_id = body.get("output_file_id")

        if status == "completed" and isinstance(output_file_id, str) and output_file_id:
            break

        if status in ("failed", "expired", "cancelled"):
            pytest.fail(f"batch ended unexpectedly with status={status}: {body}")

        await asyncio.sleep(poll_interval_s)

    if status != "completed" or not output_file_id:
        pytest.skip(f"batch did not complete within {batch_timeout_s}s (last status={status})")

    # Download output file content
    r = await _request_with_retry(client, "GET", f"/v1/files/{output_file_id}/content", headers=_auth_headers())
    assert r.status_code < 500, f"output file content returned {r.status_code}: {r.text[:200]}"
    assert r.status_code == 200, f"expected 200 for output file, got {r.status_code}: {r.text[:200]}"
    assert r.content, "output file content was empty"
```

## FILE: tests/test_images_variations_integration.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
import binascii
import os
import struct
import zlib
from typing import Dict

import pytest
import requests

RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
RELAY_TOKEN = os.getenv("RELAY_TOKEN", "")
DEFAULT_TIMEOUT_S = 20


def _auth_headers() -> Dict[str, str]:
    if not RELAY_TOKEN:
        pytest.skip("RELAY_TOKEN not set")
    return {"Authorization": f"Bearer {RELAY_TOKEN}"}


def _skip_if_no_real_key() -> None:
    # Integration tests tolerate 4xx from upstream but should not run
    # without a real OpenAI key behind the relay.
    if not os.getenv("INTEGRATION_OPENAI_API_KEY"):
        pytest.skip("INTEGRATION_OPENAI_API_KEY not set")


def _make_rgba_png_bytes(width: int, height: int, rgba=(0, 0, 0, 0)) -> bytes:
    """
    Create a minimal, valid RGBA PNG using only the standard library.
    Avoids committing binary fixtures and avoids pillow dependency.
    """
    r, g, b, a = rgba

    # Each row: filter byte (0) + width * RGBA bytes
    row = bytes([0]) + bytes([r, g, b, a]) * width
    raw = row * height
    compressed = zlib.compress(raw)

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = binascii.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack("!I", len(data)) + chunk_type + data + struct.pack("!I", crc)

    # IHDR: width, height, bit depth=8, color type=6 (RGBA), compression=0, filter=0, interlace=0
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0)

    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )


def test_openapi_has_images_variations_path() -> None:
    r = requests.get(f"{RELAY_BASE_URL}/openapi.json", timeout=DEFAULT_TIMEOUT_S)
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    assert "/v1/images/variations" in paths, "missing /v1/images/variations in OpenAPI schema"


def test_images_variations_wiring_no_5xx(tmp_path) -> None:
    _skip_if_no_real_key()

    img_path = tmp_path / "input.png"
    img_path.write_bytes(_make_rgba_png_bytes(256, 256))

    # Use an intentionally invalid model to avoid billable generations while still
    # exercising multipart wiring end-to-end.
    data = {"model": "__invalid_model__", "n": "1", "size": "256x256"}
    files = {"image": ("input.png", img_path.read_bytes(), "image/png")}

    r = requests.post(
        f"{RELAY_BASE_URL}/v1/images/variations",
        headers=_auth_headers(),
        data=data,
        files=files,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, r.text
```

## FILE: tests/test_local_e2e.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# tests/test_local_e2e.py
from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import settings
from app.main import app as fastapi_app


def _skip_if_no_openai_key() -> None:
    key = (settings.OPENAI_API_KEY or "").strip()
    normalized = key.lower()
    if not key or normalized == "dummy" or normalized.startswith("dummy"):
        pytest.skip("OPENAI_API_KEY is not set; skipping upstream-dependent local E2E tests.")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoints_ok(async_client: httpx.AsyncClient) -> None:
    paths = ["/", "/health", "/v1/health"]

    for path in paths:
        resp = await async_client.get(path)
        assert resp.status_code == 200, f"{path} returned {resp.status_code}"

        body = resp.json()
        # Top-level sanity checks
        assert body.get("object") == "health"
        assert body.get("status") == "ok"
        assert "environment" in body
        assert "default_model" in body
        assert "timestamp" in body

        # Nested structures expected by the app
        assert isinstance(body.get("relay"), dict)
        assert isinstance(body.get("openai"), dict)
        assert isinstance(body.get("meta"), dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_responses_non_streaming_basic(async_client: httpx.AsyncClient) -> None:
    _skip_if_no_openai_key()

    payload = {
        "model": settings.DEFAULT_MODEL,
        "input": "Say hello from the local relay.",
    }

    resp = await async_client.post("/v1/responses", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body.get("object") == "response"
    assert isinstance(body.get("output"), list)
    assert body["output"], "output list should not be empty"

    first_msg = body["output"][0]
    assert first_msg.get("type") == "message"
    assert first_msg.get("role") == "assistant"
    assert isinstance(first_msg.get("content"), list)
    assert first_msg["content"], "content list should not be empty"

    first_part = first_msg["content"][0]
    assert first_part.get("type") == "output_text"
    text = first_part.get("text", "")
    assert isinstance(text, str)
    assert text.strip(), "assistant text should not be empty"
    # Soft semantic check
    assert "hello" in text.lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_responses_streaming_sse_basic(async_client: httpx.AsyncClient) -> None:
    """
    Verify that the relay streams SSE events in the same shape as api.openai.com.

    We do not fully parse every event; we just assert that:
      - The HTTP status is 200
      - The SSE stream includes at least one `response.output_text.delta`
      - The SSE stream ends with `response.completed`
    """
    _skip_if_no_openai_key()

    payload = {
        "model": settings.DEFAULT_MODEL,
        "input": "Stream a short message.",
        "stream": True,
    }

    async with async_client.stream("POST", "/v1/responses", json=payload) as resp:
        assert resp.status_code == 200

        chunks: list[str] = []
        async for text_chunk in resp.aiter_text():
            chunks.append(text_chunk)

    stream_text = "".join(chunks)
    # Basic SSE framing guarantees lines starting with "event: ..."
    assert "event: response.output_text.delta" in stream_text
    assert "event: response.completed" in stream_text
    # There should also be at least one "data: " line
    assert "data:" in stream_text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_embeddings_basic(async_client: httpx.AsyncClient) -> None:
    """
    Simple check that the relay can forward /v1/embeddings and the shape matches
    OpenAI's embeddings API.
    """
    _skip_if_no_openai_key()

    payload = {
        "model": "text-embedding-3-small",
        "input": "Testing embeddings via the local relay.",
    }

    resp = await async_client.post("/v1/embeddings", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    # OpenAI embeddings responses are {"object": "list", "data": [...], ...}
    assert body.get("object") == "list"
    assert isinstance(body.get("data"), list)
    assert body["data"], "embeddings data list should not be empty"

    first_item = body["data"][0]
    assert "embedding" in first_item
    embedding = first_item["embedding"]
    assert isinstance(embedding, list)
    assert embedding, "embedding vector should not be empty"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_models_list_basic(async_client: httpx.AsyncClient) -> None:
    """
    Basic sanity check on /v1/models list endpoint.
    """
    resp = await async_client.get("/v1/models")
    assert resp.status_code == 200

    body = resp.json()
    assert body.get("object") == "list"
    assert isinstance(body.get("data"), list)

    # There should be at least one model with an "id"
    assert body["data"], "models list should not be empty"
    assert any(isinstance(m, dict) and "id" in m for m in body["data"])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_models_retrieve_default_model(async_client: httpx.AsyncClient) -> None:
    """
    Retrieve settings.DEFAULT_MODEL via /v1/models/{id} and check the shape.
    """
    model_id = settings.DEFAULT_MODEL

    resp = await async_client.get(f"/v1/models/{model_id}")
    assert resp.status_code == 200

    body = resp.json()
    assert body.get("object") == "model"
    assert body.get("id") == model_id
    # Optional extra checks if upstream includes them
    # e.g. "created", "owned_by", etc. – but we do not require them here


@pytest.mark.asyncio
@pytest.mark.integration
async def test_responses_compact_basic(async_client: httpx.AsyncClient) -> None:
    _skip_if_no_openai_key()

    payload = {
        "model": settings.DEFAULT_MODEL,
        "input": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ],
    }

    resp = await async_client.post("/v1/responses/compact", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "response.compaction"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tools_manifest_has_responses_endpoints(async_client: httpx.AsyncClient) -> None:
    resp = await async_client.get("/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert "/v1/responses" in data["endpoints"]["responses"]
    assert "/v1/responses/compact" in data["endpoints"]["responses_compact"]


@pytest.mark.asyncio
async def test_actions_images_routes_registered() -> None:
    paths = {route.path for route in fastapi_app.routes if hasattr(route, "path")}
    assert "/v1/actions/images/variations" in paths
    assert "/v1/actions/images/edits" in paths


@pytest.mark.asyncio
async def test_actions_uploads_videos_routes_registered() -> None:
    paths = {route.path for route in fastapi_app.routes if hasattr(route, "path")}
    assert "/v1/actions/uploads" in paths
    assert "/v1/actions/uploads/{upload_id}/parts" in paths
    assert "/v1/actions/uploads/{upload_id}/complete" in paths
    assert "/v1/actions/uploads/{upload_id}/cancel" in paths
    assert "/v1/actions/videos" in paths
    assert "/v1/responses:stream" in paths


@pytest.mark.asyncio
@pytest.mark.integration
async def test_actions_images_endpoints_callable(async_client: httpx.AsyncClient) -> None:
    for path in ("/v1/actions/images/variations", "/v1/actions/images/edits"):
        resp = await async_client.post(path, json={})
        assert resp.status_code == 400
        assert "Missing image input" in resp.text```

## FILE: tests/test_realtime_ws_integration.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urlsplit, urlunsplit

import pytest
import requests
from websockets import connect as ws_connect


pytestmark = pytest.mark.integration

RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
RELAY_TOKEN = os.getenv("RELAY_TOKEN", "dummy")
REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-realtime")
DEFAULT_TIMEOUT_S = float(os.getenv("RELAY_TEST_TIMEOUT_S", "60"))


def _skip_if_no_real_key() -> None:
    if os.getenv("INTEGRATION_OPENAI_API_KEY") != "1":
        pytest.skip("INTEGRATION_OPENAI_API_KEY != 1 (skipping real-API integration tests)")


def _skip_if_ws_disabled() -> None:
    if os.getenv("RELAY_REALTIME_WS_ENABLED") != "1":
        pytest.skip("RELAY_REALTIME_WS_ENABLED != 1 (realtime WS disabled)")


def _auth_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {"Authorization": f"Bearer {RELAY_TOKEN}"}
    if extra:
        headers.update(extra)
    return headers


def _must_ok(r: requests.Response, *, hint: str = "") -> None:
    if r.ok:
        return
    body = r.text
    if len(body) > 4000:
        body = body[:4000] + "…(truncated)"
    raise AssertionError(f"{hint}HTTP {r.status_code} {r.reason}: {body}")


def _extract_client_secret(payload: Dict[str, Any]) -> Optional[str]:
    candidates = [
        payload.get("client_secret"),
        payload.get("client_secret_value"),
        payload.get("clientSecret"),
        payload.get("secret"),
        payload.get("token"),
    ]

    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = value.get("value") or value.get("secret") or value.get("token")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()

    return None


def _build_ws_url(model: str, session_id: Optional[str]) -> str:
    parts = urlsplit(RELAY_BASE_URL)
    scheme = "wss" if parts.scheme == "https" else "ws"
    base = urlunsplit((scheme, parts.netloc, "", "", ""))

    query_params = {"model": model}
    if session_id:
        query_params["session_id"] = session_id

    return f"{base}/v1/realtime/ws?{urlencode(query_params)}"


async def _recv_json(websocket) -> Dict[str, Any]:
    raw = await websocket.recv()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"raw": raw}
    if not isinstance(data, dict):
        data = {"raw": data}
    return data


def _is_response_event(message: Dict[str, Any]) -> bool:
    event_type = message.get("type")
    if not isinstance(event_type, str):
        return False
    return event_type.startswith("response.") or event_type == "response"


@pytest.mark.asyncio
async def test_realtime_session_and_ws_connect_smoke() -> None:
    _skip_if_no_real_key()
    _skip_if_ws_disabled()

    r = requests.post(
        f"{RELAY_BASE_URL}/v1/realtime/sessions",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={"model": REALTIME_MODEL},
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Create realtime session failed. ")
    payload = r.json()

    session_id = payload.get("id")
    assert isinstance(session_id, str) and session_id.strip(), "Missing session id in response"

    client_secret = _extract_client_secret(payload)
    ws_url = _build_ws_url(REALTIME_MODEL, session_id)

    headers: Dict[str, str] = {}
    if client_secret:
        headers["Authorization"] = f"Bearer {client_secret}"

    async with ws_connect(ws_url, extra_headers=headers) as websocket:
        await websocket.send(json.dumps({"type": "session.update", "session": {}}))
        await websocket.send(
            json.dumps(
                {
                    "type": "response.create",
                    "response": {
                        "modalities": ["text"],
                        "instructions": "OK only",
                    },
                }
            )
        )

        response_events: list[Dict[str, Any]] = []
        deadline_s = 12
        start = asyncio.get_running_loop().time()

        while asyncio.get_running_loop().time() - start < deadline_s:
            remaining = deadline_s - (asyncio.get_running_loop().time() - start)
            message = await asyncio.wait_for(_recv_json(websocket), timeout=remaining)
            if _is_response_event(message):
                response_events.append(message)
                break

        assert response_events, "Expected at least one response.* event after response.create"
```

## FILE: tests/test_realtime_ws_local.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import time
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core import config
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    settings = config.get_settings()
    original: Dict[str, object] = {
        "RELAY_REALTIME_WS_ENABLED": settings.RELAY_REALTIME_WS_ENABLED,
        "RELAY_AUTH_ENABLED": settings.RELAY_AUTH_ENABLED,
        "RELAY_KEY": settings.RELAY_KEY,
    }

    try:
        settings.RELAY_REALTIME_WS_ENABLED = False
        settings.RELAY_AUTH_ENABLED = False
        settings.RELAY_KEY = None
        app = create_app()
        with TestClient(app) as test_client:
            yield test_client
    finally:
        settings.RELAY_REALTIME_WS_ENABLED = original["RELAY_REALTIME_WS_ENABLED"]
        settings.RELAY_AUTH_ENABLED = original["RELAY_AUTH_ENABLED"]
        settings.RELAY_KEY = original["RELAY_KEY"]


def test_realtime_session_rejects_invalid_model(client: TestClient) -> None:
    response = client.post("/v1/realtime/sessions", json={"model": "not-a-real-model"})
    assert response.status_code == 400
    body = response.json()
    assert body.get("error", {}).get("code") == "unsupported_model"


def test_realtime_local_validation_and_introspection(client: TestClient) -> None:
    response = client.post("/v1/realtime/sessions/validate", json={"session_id": "sess_valid"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"
    assert body.get("session_id") == "sess_valid"

    expired_at = time.time() - 10
    response = client.post(
        "/v1/realtime/sessions/validate",
        json={"session_id": "sess_expired", "expires_at": expired_at},
    )
    assert response.status_code == 410
    error = response.json().get("error", {})
    assert error.get("code") == "session_expired"

    response = client.get("/v1/realtime/sessions/introspect")
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"
    assert body.get("realtime_model")
    assert body.get("openai_api_base")
    assert body.get("openai_realtime_beta")
    assert body.get("now") is not None


def test_realtime_ws_disabled_closes(client: TestClient) -> None:
    with client.websocket_connect("/v1/realtime/ws?model=gpt-realtime") as websocket:
        with pytest.raises(WebSocketDisconnect) as exc:
            websocket.receive_text()
    assert exc.value.code == 1008
```

## FILE: tests/test_relay_auth_guard.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
# tests/test_relay_auth_guard.py
"""Relay auth middleware guardrails.

Why this exists
---------------
We must ensure that when RELAY_AUTH_ENABLED is turned on:

- public endpoints remain reachable without a relay key (e.g. /health)
- /v1/* endpoints require a valid relay key
- both supported auth mechanisms work:
    - Authorization: Bearer <key>
    - X-Relay-Key: <key>

This is intentionally an in-process (FastAPI TestClient) unit test so it:
- runs fast
- does not require an OpenAI API key (we test a local endpoint: /v1/models)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

pytestmark = pytest.mark.unit


def test_relay_auth_allows_health_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # Enable relay auth for this test only.
    monkeypatch.setattr(settings, "RELAY_AUTH_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "RELAY_KEY", "secret-relay-key", raising=False)

    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)

        # Health contract in this repo is {"status":"ok", ...}
        assert body.get("status") == "ok"
        assert "timestamp" in body


def test_relay_auth_requires_valid_key_for_v1_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "RELAY_AUTH_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "RELAY_KEY", "secret-relay-key", raising=False)

    with TestClient(app) as client:
        # No Authorization and no X-Relay-Key => 401
        r = client.get("/v1/models")
        assert r.status_code == 401
        assert r.json().get("detail") == "Missing relay key"

        # Authorization present but not Bearer => 401
        r = client.get("/v1/models", headers={"Authorization": "Token secret-relay-key"})
        assert r.status_code == 401
        assert "Bearer" in (r.json().get("detail") or "")

        # Wrong relay key => 401
        r = client.get("/v1/models", headers={"Authorization": "Bearer wrong-key"})
        assert r.status_code == 401
        assert r.json().get("detail") == "Invalid relay key"

        # Correct relay key via Authorization => 200
        r = client.get("/v1/models", headers={"Authorization": "Bearer secret-relay-key"})
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)
        assert body.get("object") == "list"
        assert isinstance(body.get("data"), list)

        # Correct relay key via X-Relay-Key => 200
        r = client.get("/v1/models", headers={"X-Relay-Key": "secret-relay-key"})
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)
        assert body.get("object") == "list"
```

## FILE: tests/test_remaining_routes_smoke_integration.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import os

import pytest
import requests

RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
DEFAULT_TIMEOUT_S = float(os.getenv("DEFAULT_TIMEOUT_S", "20"))


def _auth_headers(extra: dict | None = None) -> dict:
    token = os.getenv("RELAY_TOKEN") or os.getenv("RELAY_KEY") or "dummy"
    headers = {"Authorization": f"Bearer {token}"}
    if extra:
        headers.update(extra)
    return headers


@pytest.mark.integration
def test_remaining_route_families_smoke_no_5xx() -> None:
    """
    Broad smoke coverage for remaining route families.
    Goal: wiring sanity (no relay 5xx), NOT functional correctness.
    """
    endpoints = [
        ("GET", "/v1/assistants", None),
        ("GET", "/v1/threads", None),
        ("GET", "/v1/runs", None),
        ("GET", "/v1/files", None),
        ("GET", "/v1/batches", None),
        ("GET", "/v1/fine_tuning/jobs", None),
        ("GET", "/v1/audio/models", None),
        ("GET", "/v1/organization/usage", None),
    ]

    for method, path, params in endpoints:
        r = requests.request(
            method,
            f"{RELAY_BASE_URL}{path}",
            headers=_auth_headers(),
            params=params,
            timeout=DEFAULT_TIMEOUT_S,
        )
        assert r.status_code < 500, f"{method} {path} returned {r.status_code}: {r.text[:400]}"
```

## FILE: tests/test_sse_stream_open.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import asyncio
import os

import httpx
import pytest


pytestmark = pytest.mark.integration


def _require_integration() -> None:
    if os.environ.get("INTEGRATION_OPENAI_API_KEY") not in {"1", "true", "TRUE", "yes", "YES"}:
        pytest.skip("Integration tests disabled (set INTEGRATION_OPENAI_API_KEY=1)")


def _default_model() -> str:
    return os.environ.get("DEFAULT_MODEL") or "gpt-5.1"


@pytest.mark.asyncio
async def test_actions_responses_stream_sse_multiple_frames(client: httpx.AsyncClient) -> None:
    _require_integration()

    payload = {"model": _default_model(), "input": "Reply with exactly: OK"}
    max_seconds = float(os.environ.get("SSE_MAX_TIME_SECONDS") or "15")

    async with client.stream("POST", "/v1/actions/responses/stream", json=payload) as response:
        if response.status_code != 200:
            body = await response.aread()
            pytest.fail(f"expected 200, got {response.status_code}: {body[:200]!r}")

        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type.lower(), f"unexpected content-type: {content_type}"

        lines = response.aiter_lines()
        data_frames = 0
        start = asyncio.get_running_loop().time()

        while asyncio.get_running_loop().time() - start < max_seconds and data_frames < 2:
            remaining = max_seconds - (asyncio.get_running_loop().time() - start)
            try:
                line = await asyncio.wait_for(lines.__anext__(), timeout=remaining)
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                break

            if line.startswith("data:"):
                data_frames += 1

        assert data_frames >= 2, f"expected multiple SSE frames, got {data_frames}"
```

## FILE: tests/test_success_gates_integration.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import os
import time
from collections import Counter
from typing import Any, Dict, Tuple

import httpx
import pytest


def _relay_base() -> str:
    return (os.environ.get("RELAY_BASE_URL") or os.environ.get("RELAY_BASE") or "http://localhost:8000").rstrip("/")


def _relay_token() -> str:
    return os.environ.get("RELAY_TOKEN") or os.environ.get("RELAY_KEY") or "dummy"


def _default_model() -> str:
    return os.environ.get("DEFAULT_MODEL") or "gpt-5.1"


def _headers(*, accept: str | None = None, content_type: str | None = None) -> Dict[str, str]:
    h = {"Authorization": f"Bearer {_relay_token()}"}
    if accept:
        h["Accept"] = accept
    if content_type:
        h["Content-Type"] = content_type
    return h


def _require_integration() -> None:
    if os.environ.get("INTEGRATION_OPENAI_API_KEY") not in {"1", "true", "TRUE", "yes", "YES"}:
        pytest.skip("Integration tests disabled (set INTEGRATION_OPENAI_API_KEY=1)")


def _skip_if_upstream_server_error(response: httpx.Response, *, label: str) -> None:
    if response.status_code < 500:
        return
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("type") == "server_error":
            message = error.get("message") or "Upstream server error."
            pytest.skip(f"{label}: {message}")
    assert response.status_code < 500, response.text


@pytest.mark.integration
def test_gate_a_uploads_e2e_happy_and_cancel() -> None:
    _require_integration()

    base = _relay_base()
    purpose = os.environ.get("UPLOAD_PURPOSE") or "batch"
    content = b"ping"
    filename = "upload_ping.txt"

    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            f"{base}/v1/uploads",
            headers=_headers(content_type="application/json"),
            json={"purpose": purpose, "filename": filename, "bytes": len(content), "mime_type": "text/plain"},
        )
        _skip_if_upstream_server_error(r, label="Upload create failed")
        assert r.status_code == 200, r.text
        upload_id = r.json().get("id")
        assert upload_id and isinstance(upload_id, str)

        files = {"data": (filename, content, "application/octet-stream")}
        r = client.post(f"{base}/v1/uploads/{upload_id}/parts", headers=_headers(), files=files)
        assert r.status_code == 200, r.text
        part_id = r.json().get("id")
        assert part_id and isinstance(part_id, str)

        r = client.post(
            f"{base}/v1/uploads/{upload_id}/complete",
            headers=_headers(content_type="application/json"),
            json={"part_ids": [part_id]},
        )
        _skip_if_upstream_server_error(r, label="Upload complete failed")
        assert r.status_code == 200, r.text
        completed = r.json()

        file_id = None
        if isinstance(completed.get("file"), dict):
            file_id = completed["file"].get("id")
        file_id = file_id or completed.get("file_id") or completed.get("file")
        assert file_id and isinstance(file_id, str), completed

        r = client.get(f"{base}/v1/files/{file_id}/content", headers=_headers())
        assert r.status_code == 200, r.text
        assert r.content == content

        r = client.post(
            f"{base}/v1/uploads",
            headers=_headers(content_type="application/json"),
            json={"purpose": purpose, "filename": "cancel_me.txt", "bytes": len(content), "mime_type": "text/plain"},
        )
        assert r.status_code == 200, r.text
        upload2_id = r.json().get("id")
        assert upload2_id and isinstance(upload2_id, str)

        r = client.post(f"{base}/v1/uploads/{upload2_id}/cancel", headers=_headers())
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "cancelled", r.text


@pytest.mark.integration
def test_gate_b_sse_smoke() -> None:
    _require_integration()

    base = _relay_base()
    model = _default_model()

    payload = {"model": model, "input": "Write exactly: 12345678901234567890"}
    max_seconds = float(os.environ.get("SSE_MAX_TIME_SECONDS") or "15")

    with httpx.Client(timeout=max_seconds + 10) as client:
        with client.stream(
            "POST",
            f"{base}/v1/responses:stream",
            headers=_headers(accept="text/event-stream", content_type="application/json"),
            json=payload,
        ) as r:
            assert r.status_code == 200, r.read().decode("utf-8", errors="replace")
            ctype = r.headers.get("content-type", "")
            assert "text/event-stream" in ctype.lower(), ctype

            saw_data = False
            buf = b""
            start = time.time()

            for chunk in r.iter_bytes():
                if chunk:
                    buf += chunk
                    if b"data:" in buf:
                        saw_data = True
                        break
                if time.time() - start > max_seconds:
                    break

            assert saw_data, buf[:800].decode("utf-8", errors="replace")


@pytest.mark.integration
def test_gate_c_openapi_operation_ids_unique() -> None:
    base = _relay_base()

    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{base}/openapi.json")
        assert r.status_code == 200, r.text
        spec = r.json()

    paths: Dict[str, Any] = spec.get("paths", {})
    op_ids: list[Tuple[str, str, str]] = []
    for path, ops in paths.items():
        if not isinstance(ops, dict):
            continue
        for method, meta in ops.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            if not isinstance(meta, dict):
                continue
            op_id = meta.get("operationId")
            if op_id:
                op_ids.append((op_id, method.upper(), path))

    counts = Counter([x[0] for x in op_ids])
    dupes = {k: v for k, v in counts.items() if v > 1}
    if dupes:
        lines = ["Duplicate operationId values detected:"]
        for op_id in sorted(dupes.keys()):
            lines.append(f"- {op_id}")
            for _, method, path in [x for x in op_ids if x[0] == op_id]:
                lines.append(f"    {method} {path}")
        raise AssertionError("\n".join(lines))


@pytest.mark.integration
def test_gate_d_content_endpoints_wiring_negative_ids() -> None:
    _require_integration()

    base = _relay_base()

    def check(url: str) -> None:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(url, headers=_headers())
            assert r.status_code != 500, r.text
            assert "application/json" in (r.headers.get("content-type") or "").lower(), r.headers
            body = r.json()
            assert isinstance(body, dict) and "error" in body and "message" in body["error"], body

    check(f"{base}/v1/containers/cont_invalid/files/file_invalid/content")
    check(f"{base}/v1/videos/video_invalid/content")
```

## FILE: tests/test_videos_actions_integration.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
from __future__ import annotations

import base64
import os
from typing import Any, Dict

import httpx
import pytest

from app.routes.videos import (
    _ALLOWED_VIDEO_MODELS,
    _ALLOWED_VIDEO_SECONDS,
    _ALLOWED_VIDEO_SIZES,
    _MAX_DURATION_SECONDS,
    _MAX_FRAMES,
    _MAX_VIDEO_BYTES,
)


pytestmark = pytest.mark.integration


def _is_openai_error(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    error = payload.get("error")
    if not isinstance(error, dict):
        return False
    message = error.get("message")
    err_type = error.get("type")
    return isinstance(message, str) and isinstance(err_type, str)


def _assert_4xx_openai_error(response: httpx.Response) -> None:
    assert 400 <= response.status_code < 500, f"expected 4xx, got {response.status_code}: {response.text[:200]}"
    try:
        payload = response.json()
    except Exception:
        pytest.fail(f"expected JSON error payload, got: {response.text[:200]}")
    assert _is_openai_error(payload), f"expected OpenAI-shaped error, got: {payload}"


def _payload_over_max_bytes() -> str:
    raw = b"x" * (_MAX_VIDEO_BYTES + 1)
    return base64.b64encode(raw).decode("utf-8")


@pytest.mark.asyncio
async def test_actions_videos_generations_rejects_invalid_inputs(client: httpx.AsyncClient) -> None:
    url = "/v1/actions/videos/generations"
    base_payload = {"prompt": "A test prompt"}

    invalid_base64 = {**base_payload, "data_base64": "not-base64!!"}
    r = await client.post(url, json=invalid_base64)
    _assert_4xx_openai_error(r)

    empty_bytes = {**base_payload, "data_base64": ""}
    r = await client.post(url, json=empty_bytes)
    _assert_4xx_openai_error(r)

    oversized = {**base_payload, "data_base64": _payload_over_max_bytes()}
    r = await client.post(url, json=oversized)
    _assert_4xx_openai_error(r)

    too_many_frames = {**base_payload, "frames": _MAX_FRAMES + 1}
    r = await client.post(url, json=too_many_frames)
    _assert_4xx_openai_error(r)

    too_long_duration = {**base_payload, "duration_seconds": _MAX_DURATION_SECONDS + 1}
    r = await client.post(url, json=too_long_duration)
    _assert_4xx_openai_error(r)

    invalid_model = {**base_payload, "model": "invalid-model"}
    r = await client.post(url, json=invalid_model)
    _assert_4xx_openai_error(r)

    invalid_seconds = {**base_payload, "seconds": max(_ALLOWED_VIDEO_SECONDS) + 1}
    r = await client.post(url, json=invalid_seconds)
    _assert_4xx_openai_error(r)

    invalid_size = {**base_payload, "size": "999x999"}
    r = await client.post(url, json=invalid_size)
    _assert_4xx_openai_error(r)
```

## BASELINE (static/)

## FILE: static/.well-known/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
```

## FILE: static/.well-known/ai-plugin.json @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
{
  "schema_version": "v1",
  "name_for_human": "ChatGPT Team Relay",
  "name_for_model": "chatgpt_team_relay",
  "description_for_human": "A relay that forwards ChatGPT-style requests to the OpenAI API with custom routing, logging, and tools.",
  "description_for_model": "You are calling a relay service that forwards requests to the OpenAI API. Prefer the /v1/responses endpoint for chat-style interactions. Use /v1/tools to discover available actions and /v1/realtime/sessions only when you need a realtime session.",
  "auth": {
    "type": "none"
  },
  "api": {
    "type": "openapi",
    "url": "https://chatgpt-team-relay.onrender.com/openapi.yaml",
    "has_user_authentication": false
  },
  "logo_url": "https://chatgpt-team-relay.onrender.com/static/logo.png",
  "contact_email": "support@example.com",
  "legal_info_url": "https://example.com/legal",
  "terms_of_service_url": "https://example.com/terms",
  "privacy_policy_url": "https://example.com/privacy",
  "settings": {
    "use_user_consent_on_first_use": false
  }
}
```

## BASELINE (schemas/)

## FILE: schemas/__init__.py @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
```

## FILE: schemas/openapi.yaml @ 3896cd6f44a7da6c58071c889574a3d5723c4363
```
openapi: 3.1.0
info:
  title: ChatGPT Team Relay
  version: "1.0.0"
  description: |
    OpenAPI description for the ChatGPT Team Relay.

    This relay exposes a thin, OpenAI-compatible proxy surface:

      • /v1/responses
      • /v1/embeddings
      • /v1/models
      • /v1/files
      • /v1/vector_stores
      • /v1/images
      • /v1/videos
      • /v1/conversations
      • /v1/realtime/sessions

    It also provides local utility endpoints under /actions and /v1/actions
    plus a tools manifest at /v1/tools for ChatGPT Actions.

servers:
  - url: https://chatgpt-team-relay.onrender.com

paths:
  /health:
    get:
      operationId: getHealth
      summary: Health check
      responses:
        "200":
          description: Relay is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  mode:
                    type: string
                  environment:
                    type: string

  /v1/health:
    get:
      operationId: getHealthV1
      summary: v1-style health check
      responses:
        "200":
          description: Relay is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  mode:
                    type: string
                  environment:
                    type: string

  /v1/responses:
    post:
      operationId: createResponse
      summary: Create a response
      description: |
        Thin proxy to the OpenAI Responses API.
        Supports both non-stream and stream=true modes.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              description: OpenAI Responses request payload.
      responses:
        "200":
          description: Response object from the OpenAI Responses API
          content:
            application/json:
              schema:
                type: object

  /v1/responses:stream:
    post:
      operationId: streamResponse
      summary: Stream a response (SSE)
      description: |
        Wrapper that forces stream=true and proxies to /v1/responses.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: SSE stream of response events
          content:
            text/event-stream:
              schema:
                type: string

  /v1/responses/{response_id}:
    get:
      operationId: retrieveResponse
      summary: Retrieve a response by ID
      parameters:
        - name: response_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Response object
          content:
            application/json:
              schema:
                type: object

  /v1/responses/{response_id}/cancel:
    post:
      operationId: cancelResponse
      summary: Cancel a running response
      parameters:
        - name: response_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Cancellation acknowledgement
          content:
            application/json:
              schema:
                type: object

  /v1/embeddings:
    post:
      operationId: createEmbedding
      summary: Create embeddings
      description: Thin proxy to the OpenAI Embeddings API.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Embedding result
          content:
            application/json:
              schema:
                type: object

  /v1/models:
    get:
      operationId: listModels
      summary: List models
      responses:
        "200":
          description: List of models
          content:
            application/json:
              schema:
                type: object

  /v1/models/{model_id}:
    get:
      operationId: retrieveModel
      summary: Retrieve a model
      parameters:
        - name: model_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Model details
          content:
            application/json:
              schema:
                type: object

  /v1/files:
    get:
      operationId: listFiles
      summary: List files
      responses:
        "200":
          description: List of files
          content:
            application/json:
              schema:
                type: object
    post:
      operationId: createFile
      summary: Upload a file
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: File metadata
          content:
            application/json:
              schema:
                type: object

  /v1/files/{file_id}:
    get:
      operationId: retrieveFile
      summary: Retrieve file metadata
      parameters:
        - name: file_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: File metadata
          content:
            application/json:
              schema:
                type: object
    delete:
      operationId: deleteFile
      summary: Delete a file
      parameters:
        - name: file_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: File deletion confirmation
          content:
            application/json:
              schema:
                type: object

  /v1/vector_stores:
    get:
      operationId: listVectorStores
      summary: List vector stores
      responses:
        "200":
          description: List of vector stores
          content:
            application/json:
              schema:
                type: object
    post:
      operationId: createVectorStore
      summary: Create a vector store
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Vector store object
          content:
            application/json:
              schema:
                type: object

  /v1/vector_stores/{vector_store_id}:
    get:
      operationId: retrieveVectorStore
      summary: Retrieve a vector store
      parameters:
        - name: vector_store_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Vector store object
          content:
            application/json:
              schema:
                type: object

  /v1/images:
    post:
      operationId: createImagesRoot
      summary: Best-effort image generation entrypoint
      description: Thin proxy to the OpenAI Images API for legacy clients.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Image generation response
          content:
            application/json:
              schema:
                type: object

  /v1/images/generations:
    post:
      operationId: createImageGenerations
      summary: Generate images from a prompt
      description: Thin proxy to the OpenAI Images /images/generations endpoint.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Image generation response
          content:
            application/json:
              schema:
                type: object

  /v1/videos:
    post:
      operationId: createVideoJob
      summary: Create a video generation job
      description: Thin proxy to the OpenAI Videos API (job creation).
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Video job object
          content:
            application/json:
              schema:
                type: object

  /v1/videos/{video_path}:
    get:
      operationId: getVideoJobOrContent
      summary: Retrieve a video job or content
      parameters:
        - name: video_path
          in: path
          required: true
          schema:
            type: string
          description: |
            Path under /v1/videos, e.g. "jobs/{id}", "jobs/{id}/content".
      responses:
        "200":
          description: Video job or content
          content:
            application/json:
              schema:
                type: object

  /v1/conversations:
    get:
      operationId: listConversations
      summary: List conversations
      responses:
        "200":
          description: List of conversations
          content:
            application/json:
              schema:
                type: object
    post:
      operationId: createConversation
      summary: Create a conversation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Conversation object
          content:
            application/json:
              schema:
                type: object

  /v1/conversations/{conversation_id}:
    get:
      operationId: retrieveConversation
      summary: Retrieve a conversation
      parameters:
        - name: conversation_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Conversation object
          content:
            application/json:
              schema:
                type: object
    delete:
      operationId: deleteConversation
      summary: Delete a conversation
      parameters:
        - name: conversation_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Deletion confirmation
          content:
            application/json:
              schema:
                type: object

  /v1/conversations/{conversation_id}/messages:
    get:
      operationId: listConversationMessages
      summary: List messages in a conversation
      parameters:
        - name: conversation_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: List of messages
          content:
            application/json:
              schema:
                type: object
    post:
      operationId: createConversationMessage
      summary: Add a message to a conversation
      parameters:
        - name: conversation_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Message object
          content:
            application/json:
              schema:
                type: object

  /v1/realtime/sessions:
    post:
      operationId: createRealtimeSession
      summary: Create a Realtime session
      description: Thin proxy to the OpenAI Realtime Sessions API.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Realtime session object
          content:
            application/json:
              schema:
                type: object

  /v1/tools:
    get:
      operationId: listTools
      summary: List tools from the tools manifest
      responses:
        "200":
          description: List of tools
          content:
            application/json:
              schema:
                type: object

  /v1/tools/{tool_id}:
    get:
      operationId: retrieveTool
      summary: Retrieve a single tool definition
      parameters:
        - name: tool_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Tool definition
          content:
            application/json:
              schema:
                type: object

  /actions/ping:
    get:
      operationId: actionsPing
      summary: Simple ping at /actions
      responses:
        "200":
          description: Ping OK
          content:
            application/json:
              schema:
                type: object

  /v1/actions/ping:
    get:
      operationId: v1ActionsPing
      summary: Simple ping at /v1/actions
      responses:
        "200":
          description: Ping OK
          content:
            application/json:
              schema:
                type: object

  /actions/relay_info:
    get:
      operationId: actionsRelayInfo
      summary: Relay information (actions)
      responses:
        "200":
          description: Relay info object
          content:
            application/json:
              schema:
                type: object

  /v1/actions/relay_info:
    get:
      operationId: v1ActionsRelayInfo
      summary: Relay information (v1/actions)
      responses:
        "200":
          description: Relay info object
          content:
            application/json:
              schema:
                type: object

  /v1/actions/uploads:
    post:
      operationId: actionsCreateUpload
      summary: Create an upload (Actions wrapper)
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Upload object
          content:
            application/json:
              schema:
                type: object

  /v1/actions/uploads/{upload_id}/parts:
    post:
      operationId: actionsCreateUploadPart
      summary: Create an upload part (Actions wrapper)
      parameters:
        - name: upload_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Upload part object
          content:
            application/json:
              schema:
                type: object

  /v1/actions/uploads/{upload_id}/complete:
    post:
      operationId: actionsCompleteUpload
      summary: Complete an upload (Actions wrapper)
      parameters:
        - name: upload_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Upload completion result
          content:
            application/json:
              schema:
                type: object

  /v1/actions/uploads/{upload_id}/cancel:
    post:
      operationId: actionsCancelUpload
      summary: Cancel an upload (Actions wrapper)
      parameters:
        - name: upload_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Upload cancellation result
          content:
            application/json:
              schema:
                type: object

  /v1/actions/videos:
    post:
      operationId: actionsCreateVideo
      summary: Create a video (Actions wrapper)
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Video job object
          content:
            application/json:
              schema:
                type: object

components: {}```

## BASELINE (src/)

## BASELINE (scripts/src/)

