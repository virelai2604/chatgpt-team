# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 834ed1053166c0c0551d2195ee113f003ee84712
Dirs: app tests static schemas src scripts/src
Root files: project-tree.md pyproject.toml chatgpt_sync.sh AGENTS.md __init__.py generate_tree.py
Mode: baseline
Generated: 2025-12-25T11:07:57+07:00

## TREE (repo root at 834ed1053166c0c0551d2195ee113f003ee84712)
```
 - .env.example.env
 - .gitattributes
 - .github
 - .gitignore
 - .gitleaks.toml
 - AGENTS.md
 - ChatGPT-API_reference_ground_truth-2025-10-29.pdf
 - RELAY_CHECKLIST_v16.md
 - RELAY_PROGRESS_SUMMARY_v12.md
 - __init__.py
 - app
 - chatgpt_baseline.md
 - chatgpt_changes.md
 - chatgpt_sync.sh
 - data
 - docs
 - generate_tree.py
 - input.png
 - input_256.png
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

## TREE (app/ at 834ed1053166c0c0551d2195ee113f003ee84712)
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

## TREE (tests/ at 834ed1053166c0c0551d2195ee113f003ee84712)
```
 - tests/__init__.py
 - tests/client.py
 - tests/conftest.py
 - tests/test_extended_routes_smoke_integration.py
 - tests/test_files_and_batches_integration.py
 - tests/test_images_variations_integration.py
 - tests/test_local_e2e.py
 - tests/test_relay_auth_guard.py
 - tests/test_remaining_routes_smoke_integration.py
 - tests/test_success_gates_integration.py
```

## TREE (static/ at 834ed1053166c0c0551d2195ee113f003ee84712)
```
 - static/.well-known/__init__.py
 - static/.well-known/ai-plugin.json
```

## TREE (schemas/ at 834ed1053166c0c0551d2195ee113f003ee84712)
```
 - schemas/__init__.py
 - schemas/openapi.yaml
```

## TREE (src/ at 834ed1053166c0c0551d2195ee113f003ee84712)
```
```

## TREE (scripts/src/ at 834ed1053166c0c0551d2195ee113f003ee84712)
```
```

## BASELINE (ROOT FILES)

## FILE: project-tree.md @ 834ed1053166c0c0551d2195ee113f003ee84712
```
  📄 .env.env
  📄 .env.example.env
  📄 .gitattributes
  📄 .gitignore
  📄 .gitleaks.toml
  📄 AGENTS.md
  📄 ChatGPT-API_reference_ground_truth-2025-10-29.pdf
  📄 RELAY_CHECKLIST_v16.md
  📄 RELAY_PROGRESS_SUMMARY_v12.md
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
  📁 schemas
    📄 __init__.py
    📄 openapi.yaml
  📁 scripts
    📄 batch_download_test.sh
    📄 content_endpoints_smoke.sh
    📄 openapi_operationid_check.sh
    📄 run_success_gates.sh
    📄 sse_smoke_test.sh
    📄 test_local.sh
    📄 test_render.sh
    📄 test_success_gates_integration.sh
    📄 uploads_e2e_test.sh
  📁 static
    📁 .well-known
      📄 __init__.py
      📄 ai-plugin.json
  📁 tests
    📄 __init__.py
    📄 client.py
    📄 conftest.py
    📄 test_extended_routes_smoke_integration.py
    📄 test_files_and_batches_integration.py
    📄 test_local_e2e.py
    📄 test_relay_auth_guard.py
    📄 test_remaining_routes_smoke_integration.py
    📄 test_success_gates_integration.py```

## FILE: pyproject.toml @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: chatgpt_sync.sh @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: AGENTS.md @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: __init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
```

## FILE: generate_tree.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
```

## FILE: app/api/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
```

## FILE: app/api/forward_openai.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from __future__ import annotations

import gzip
import json
import zlib
from typing import Any, AsyncIterator, Dict, Mapping, Optional
from urllib.parse import urlencode

import httpx
from fastapi import Request
from fastapi.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client

# ---------------------------------------------------------------------------
# Header handling
# ---------------------------------------------------------------------------

_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}

# We strip Content-Encoding because the relay requests identity upstream and/or
# returns decoded bytes. Keeping Content-Encoding while returning identity bytes
# can break downstream clients (e.g., requests json()).
_STRIP_RESPONSE_HEADERS = {
    *_HOP_BY_HOP_HEADERS,
    "content-encoding",
}


def _get_setting(settings: object, *names: str, default=None):
    """Return the first non-empty attribute among several possible setting names."""
    for name in names:
        if hasattr(settings, name):
            val = getattr(settings, name)
            if val is not None and str(val).strip() != "":
                return val
    return default


def _openai_base_url(settings: object) -> str:
    return str(
        _get_setting(
            settings,
            "OPENAI_BASE_URL",
            "OPENAI_API_BASE",
            "openai_base_url",
            "openai_api_base",
            default="https://api.openai.com/v1",
        )
    ).rstrip("/")


def _openai_api_key(settings: object) -> str:
    key = _get_setting(settings, "OPENAI_API_KEY", "openai_api_key", default="")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return str(key)


def _join_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    path = "/" + path.lstrip("/")
    # Avoid /v1/v1 duplication
    if base.endswith("/v1") and path.startswith("/v1/"):
        path = path[len("/v1") :]
    return base + path


def _get_timeout_seconds(settings: object) -> float:
    """Compatibility helper used by some route modules."""
    return float(
        _get_setting(
            settings,
            "PROXY_TIMEOUT_SECONDS",
            "proxy_timeout_seconds",
            "PROXY_TIMEOUT",
            "RELAY_TIMEOUT_SECONDS",
            "RELAY_TIMEOUT",
            default=90.0,
        )
    )


def build_upstream_url(
    path: str,
    *,
    request: Optional[Request] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    Build a full upstream OpenAI URL for the given API path.

    - Handles bases with or without `/v1`
    - Preserves the inbound query string when `request` is provided
    """
    s = get_settings()
    base = (base_url or _openai_base_url(s)).rstrip("/")
    url = _join_url(base, path)

    if request is not None and request.url.query:
        url = url + "?" + request.url.query

    return url


def build_outbound_headers(
    *,
    inbound_headers: Mapping[str, str],
    content_type: Optional[str] = None,
    forward_accept: bool = True,
    accept: Optional[str] = None,
    accept_encoding: str = "identity",
    path_hint: Optional[str] = None,  # compatibility; not used
) -> Dict[str, str]:
    """
    Build upstream request headers.

    Key behavior:
      - Never forward client Authorization upstream.
      - Never forward client Accept-Encoding upstream.
      - Force relay's server-side OpenAI API key.
      - Default Accept-Encoding to identity to avoid brotli/br responses that
        some clients cannot decode.
    """
    s = get_settings()

    out: Dict[str, str] = {}

    for k, v in inbound_headers.items():
        lk = k.lower()

        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk == "authorization":
            continue
        if lk == "accept-encoding":
            continue

        # We'll set Accept/Content-Type explicitly below.
        if lk == "accept":
            continue
        if lk == "content-type":
            # Preserve multipart boundary etc unless caller overrides.
            if content_type is None:
                out[k] = v
            continue

        out[k] = v

    # Force upstream OpenAI key.
    out["Authorization"] = f"Bearer {_openai_api_key(s)}"

    # Optional org/project/beta headers from config.
    org = _get_setting(s, "OPENAI_ORG", "OPENAI_ORGANIZATION", "openai_organization", default=None)
    if org:
        out["OpenAI-Organization"] = str(org)

    project = _get_setting(s, "OPENAI_PROJECT", "openai_project", default=None)
    if project:
        out["OpenAI-Project"] = str(project)

    beta = _get_setting(s, "OPENAI_BETA", "openai_beta", default=None)
    if beta:
        out["OpenAI-Beta"] = str(beta)

    # Accept header
    if forward_accept:
        inbound_accept = None
        try:
            inbound_accept = inbound_headers.get("accept")  # type: ignore[attr-defined]
        except Exception:
            inbound_accept = None
        out["Accept"] = accept or inbound_accept or "*/*"

    # Critical: avoid br/brotli unless we can guarantee decode support everywhere.
    out["Accept-Encoding"] = accept_encoding

    # Content-Type override (when caller explicitly sets it).
    if content_type is not None and content_type.strip() != "":
        out["Content-Type"] = content_type

    return out


def filter_upstream_headers(up_headers: httpx.Headers) -> Dict[str, str]:
    """Filter upstream response headers to forward back to the client safely."""
    out: Dict[str, str] = {}
    for k, v in up_headers.items():
        lk = k.lower()
        if lk in _STRIP_RESPONSE_HEADERS:
            continue
        out[k] = v
    return out


def _maybe_model_dump(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


# ---------------------------------------------------------------------------
# Response body hardening (defensive decoding)
# ---------------------------------------------------------------------------

_JSON_FIRST_BYTES = set(b'{["-0123456789tfn')


def _looks_like_json(data: bytes) -> bool:
    if not data:
        return False
    i = 0
    ln = len(data)
    while i < ln and data[i] in b" \t\r\n":
        i += 1
    if i >= ln:
        return False
    return data[i] in _JSON_FIRST_BYTES


def _decode_content_by_encoding(data: bytes, encoding: str) -> bytes:
    """
    Best-effort decode for common HTTP Content-Encoding values.

    Note: In normal operation we request Accept-Encoding: identity upstream and/or rely on httpx to decode.
    This helper exists only as a defensive fallback for misbehaving proxies.
    """
    if not data:
        return data

    # Multiple encodings can be comma-separated; decode in reverse application order.
    encs = [e.strip().lower() for e in (encoding or "").split(",") if e.strip()]
    if not encs:
        return data

    for enc in reversed(encs):
        if enc in {"identity", "none"}:
            continue

        if enc == "gzip":
            try:
                data = gzip.decompress(data)
                continue
            except Exception:
                # Some servers lie and send zlib-wrapped deflate with gzip header.
                try:
                    data = zlib.decompress(data, wbits=16 + zlib.MAX_WBITS)
                    continue
                except Exception:
                    return data

        if enc == "deflate":
            # Try zlib-wrapped first, then raw deflate.
            try:
                data = zlib.decompress(data)
                continue
            except Exception:
                try:
                    data = zlib.decompress(data, wbits=-zlib.MAX_WBITS)
                    continue
                except Exception:
                    return data

        if enc == "br":
            # Optional dependency; only decode if available.
            brotli = None
            try:
                import brotli as brotli_lib  # type: ignore
                brotli = brotli_lib
            except Exception:
                try:
                    import brotlicffi as brotli_lib  # type: ignore
                    brotli = brotli_lib
                except Exception:
                    brotli = None

            if brotli is None:
                return data

            try:
                data = brotli.decompress(data)  # type: ignore[attr-defined]
                continue
            except Exception:
                return data

        # Unknown encoding: bail out.
        return data

    return data


# ---------------------------------------------------------------------------
# Core forwarders
# ---------------------------------------------------------------------------

async def forward_openai_request(request: Request) -> Response:
    """
    Raw HTTP passthrough to the upstream OpenAI API.

    Supports:
      - JSON + multipart requests
      - SSE streaming when upstream returns text/event-stream

    Hardening:
      - Forces Accept-Encoding=identity upstream (avoids brotli responses that
        break some clients / test harnesses).
      - Never raises on upstream non-2xx; returns upstream status + body.
    """
    upstream_url = build_upstream_url(request.url.path, request=request)

    # Preserve inbound Content-Type unless caller wants to override; this keeps
    # multipart boundaries intact.
    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        accept_encoding="identity",
    )

    # Only send a body for methods that can carry one.
    body_bytes: Optional[bytes]
    if request.method.upper() in {"GET", "HEAD"}:
        body_bytes = None
    else:
        body_bytes = await request.body()

    timeout_s = _get_timeout_seconds(get_settings())
    client = get_async_httpx_client(timeout=timeout_s)

    upstream_req = client.build_request(
        method=request.method.upper(),
        url=upstream_url,
        headers=headers,
        content=body_bytes,
    )

    upstream = await client.send(upstream_req, stream=True)
    media_type = upstream.headers.get("content-type")

    # SSE streaming
    if media_type and "text/event-stream" in media_type.lower():

        async def gen() -> AsyncIterator[bytes]:
            try:
                async for chunk in upstream.aiter_bytes():
                    yield chunk
            finally:
                await upstream.aclose()

        return StreamingResponse(
            gen(),
            status_code=upstream.status_code,
            headers=filter_upstream_headers(upstream.headers),
            media_type=media_type,
        )

    # Non-SSE: return buffered content (small JSON payloads, errors, etc.)
    try:
        data = await upstream.aread()
    finally:
        await upstream.aclose()

    # Defensive: if upstream still returns encoded bytes (rare), try to decode.
    content_encoding = upstream.headers.get("content-encoding") or ""
    if content_encoding and media_type and "application/json" in media_type.lower():
        if not _looks_like_json(data):
            data = _decode_content_by_encoding(data, content_encoding)

    return Response(
        content=data,
        status_code=upstream.status_code,
        headers=filter_upstream_headers(upstream.headers),
        media_type=media_type,
    )


async def forward_openai_method_path(
    method: str,
    path: str,
    request: Optional[Request] = None,
    *,
    query: Optional[Mapping[str, Any]] = None,
    json_body: Optional[Any] = None,
    body: Optional[Any] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    JSON-focused forwarder used by /v1/proxy and a few compatibility routes.

    Supports multiple call styles that exist in the codebase:
      - forward_openai_method_path("POST", "/v1/videos", request)
      - forward_openai_method_path(method="POST", path="/v1/responses", query=..., json_body=..., inbound_headers=...)
    """
    s = get_settings()
    base_url = _openai_base_url(s)
    url = _join_url(base_url, path)

    if query:
        url = url + "?" + urlencode(query, doseq=True)

    headers_source: Mapping[str, str]
    if inbound_headers is not None:
        headers_source = inbound_headers
    elif request is not None:
        headers_source = request.headers
    else:
        headers_source = {}

    # Prefer json_body, fall back to body for legacy callers.
    payload = json_body if json_body is not None else body

    content: Optional[bytes] = None
    content_type: Optional[str] = None

    m = method.strip().upper()
    if m not in {"GET", "HEAD"}:
        if payload is None:
            content = None
        elif isinstance(payload, (bytes, bytearray)):
            content = bytes(payload)
        else:
            content = json.dumps(payload).encode("utf-8")
            content_type = "application/json"

    headers = build_outbound_headers(
        inbound_headers=headers_source,
        content_type=content_type,
        forward_accept=True,
        accept_encoding="identity",
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)
    upstream = await client.request(m, url, headers=headers, content=content)

    data = upstream.content
    media_type = upstream.headers.get("content-type")
    content_encoding = upstream.headers.get("content-encoding") or ""
    if content_encoding and media_type and "application/json" in media_type.lower():
        if not _looks_like_json(data):
            data = _decode_content_by_encoding(data, content_encoding)

    return Response(
        content=data,
        status_code=upstream.status_code,
        headers=filter_upstream_headers(upstream.headers),
        media_type=media_type,
    )


# ---------------------------------------------------------------------------
# Typed helpers (openai-python SDK)
# ---------------------------------------------------------------------------

async def forward_responses_create(payload: Dict[str, Any]) -> Any:
    """
    Typed helper for non-streaming /v1/responses.

    Some routers import this symbol directly (keep stable).
    """
    client = get_async_openai_client()
    result = await client.responses.create(**payload)
    return _maybe_model_dump(result)


async def forward_embeddings_create(payload: Dict[str, Any]) -> Any:
    client = get_async_openai_client()
    result = await client.embeddings.create(**payload)
    return _maybe_model_dump(result)


__all__ = [
    "_get_timeout_seconds",
    "build_outbound_headers",
    "build_upstream_url",
    "filter_upstream_headers",
    "forward_openai_request",
    "forward_openai_method_path",
    "forward_responses_create",
    "forward_embeddings_create",
]
```

## FILE: app/api/routes.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
# app/api/routes.py

from __future__ import annotations

from fastapi import APIRouter

from app.routes.register_routes import register_routes
from app.utils.logger import get_logger

logger = get_logger(__name__)

# This router is included by app.main and mirrors all route families under /v1.
router = APIRouter()

# Delegate wiring to the shared register_routes helper.
register_routes(router)

logger.info("API router initialized with shared route families")
```

## FILE: app/api/sse.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
# app/api/sse.py
from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Iterable, Optional, Union

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from app.core.http_client import get_async_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["openai-relay-streaming"])

SSEByteSource = Union[Iterable[bytes], AsyncIterator[bytes]]


def format_sse_event(
    *,
    event: str,
    data: str,
    id: Optional[str] = None,
    retry: Optional[int] = None,
) -> bytes:
    lines = []
    if id is not None:
        lines.append(f"id: {id}")
    if event:
        lines.append(f"event: {event}")

    if data == "":
        lines.append("data:")
    else:
        for line in data.splitlines():
            lines.append(f"data: {line}")

    if retry is not None:
        lines.append(f"retry: {retry}")

    payload = "\n".join(lines) + "\n\n"
    return payload.encode("utf-8")


def sse_error_event(message: str, code: Optional[str] = None, *, id: Optional[str] = None) -> bytes:
    payload = {"message": message}
    if code:
        payload["code"] = code
    data_str = ";".join([f"{k}={v}" for k, v in payload.items()])
    return format_sse_event(event="error", data=data_str, id=id)


class StreamingSSE(StreamingResponse):
    def __init__(self, content: SSEByteSource, status_code: int = 200, headers: Optional[dict] = None) -> None:
        super().__init__(content=content, status_code=status_code, headers=headers, media_type="text/event-stream")


# Compatibility shim: some older modules imported create_sse_stream from app.api.sse
def create_sse_stream(
    content: SSEByteSource,
    *,
    status_code: int = 200,
    headers: Optional[dict] = None,
) -> StreamingSSE:
    return StreamingSSE(content=content, status_code=status_code, headers=headers)


async def _responses_event_stream(payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    client = get_async_openai_client()
    logger.info("Streaming /v1/responses:stream with payload: %s", payload)

    p = dict(payload)
    p.setdefault("stream", True)

    stream = await client.responses.create(**p)  # stream=True above

    async for event in stream:
        if hasattr(event, "model_dump_json"):
            data_json = event.model_dump_json()
        elif hasattr(event, "model_dump"):
            data_json = json.dumps(event.model_dump(), default=str, separators=(",", ":"))
        else:
            try:
                data_json = json.dumps(event, default=str, separators=(",", ":"))
            except TypeError:
                data_json = json.dumps(str(event))

        yield f"data: {data_json}\n\n".encode("utf-8")

    yield b"data: [DONE]\n\n"


@router.post("/responses:stream")
async def responses_stream(
    body: Dict[str, Any] = Body(..., description="OpenAI Responses.create payload for streaming"),
) -> StreamingSSE:
    return StreamingSSE(_responses_event_stream(body))
```

## FILE: app/api/tools_api.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
# ==========================================================
# app/api/tools_api.py — Tools Manifest Endpoints
# ==========================================================
"""
Serves the relay's tools manifest at:
  - GET /manifest
  - GET /v1/manifest

Intent:
  - Option A (Actions-friendly): expose a small, JSON-only tool surface.
  - Full route inventory lives in OpenAPI at /openapi.json.

The integration tests expect:
  data["endpoints"]["responses"] includes "/v1/responses"
  data["endpoints"]["responses_compact"] includes "/v1/responses/compact"
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from fastapi import APIRouter

from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["manifest"])


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_tools(payload: Any) -> List[Dict[str, Any]]:
    """
    Accept multiple on-disk shapes safely:
      - {"tools": [...]}                       (legacy)
      - {"data": [...], "object": "list", ...} (what /manifest returns)
      - [...]                                   (raw list of tool dicts)
    """
    if isinstance(payload, list):
        return cast(List[Dict[str, Any]], payload)

    if isinstance(payload, dict):
        tools = payload.get("tools")
        if isinstance(tools, list):
            return cast(List[Dict[str, Any]], tools)

        data = payload.get("data")
        if isinstance(data, list):
            return cast(List[Dict[str, Any]], data)

    return []


def load_tools_manifest() -> List[Dict[str, Any]]:
    """
    Loads tools from:
      1) settings.TOOLS_MANIFEST (if it's a list of tools)
      2) settings.TOOLS_MANIFEST (if it's a path to JSON)
      3) fallback: app/manifests/tools_manifest.json
    """
    settings = get_settings()
    manifest_setting: Union[str, List[Dict[str, Any]], None] = getattr(settings, "TOOLS_MANIFEST", None)

    # If someone injected the tools directly (already parsed)
    if isinstance(manifest_setting, list):
        return manifest_setting

    # If it's a path string
    if isinstance(manifest_setting, str) and manifest_setting.strip():
        path = Path(manifest_setting)
        if path.exists():
            try:
                return _extract_tools(_read_json(path))
            except Exception as e:
                logger.warning("Failed reading TOOLS_MANIFEST from %s: %s", path, e)

    # Fallback to app/manifests/tools_manifest.json relative to this file
    fallback_path = Path(__file__).resolve().parents[1] / "manifests" / "tools_manifest.json"
    if fallback_path.exists():
        try:
            return _extract_tools(_read_json(fallback_path))
        except Exception as e:
            logger.warning("Failed reading fallback tools manifest from %s: %s", fallback_path, e)

    return []


def build_manifest_response(tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    settings = get_settings()
    tools_list = tools if tools is not None else load_tools_manifest()

    # Keep current behavior for tests and clients.
    endpoints: Dict[str, List[str]] = {
        # Option A: single Action-friendly proxy entrypoint.
        "proxy": ["/v1/proxy"],
        "responses": ["/v1/responses", "/v1/responses/compact"],
        "responses_compact": ["/v1/responses/compact"],
    }

    relay_name = (
        getattr(settings, "relay_name", None)
        or getattr(settings, "project_name", None)
        or "ChatGPT Team Relay"
    )

    # IMPORTANT: We intentionally do not list multipart/binary families (e.g., /v1/uploads)
    # in this tools manifest. Those routes may exist in the app (see /openapi.json) but are
    # excluded from the Actions-safe tool surface by design.
    meta: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "relay_name": relay_name,
        "manifest_scope": "actions_safe",
        "option": "A",
        "openapi_url": "/openapi.json",
        "endpoints_note": (
            "This manifest is a curated, JSON-only tool surface. "
            "Multipart/binary route families (e.g., Uploads) are intentionally excluded; "
            "refer to /openapi.json for the full route inventory."
        ),
    }

    return {
        "object": "list",
        "data": tools_list,
        "endpoints": endpoints,
        "meta": meta,
    }


@router.get("/manifest")
async def get_manifest_root() -> Dict[str, Any]:
    logger.info("Serving tools manifest (root alias)")
    return build_manifest_response()


@router.get("/v1/manifest")
async def get_manifest_v1() -> Dict[str, Any]:
    logger.info("Serving tools manifest (/v1)")
    return build_manifest_response()
```

## FILE: app/core/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
```

## FILE: app/core/config.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read an environment variable with whitespace/empty-string normalization."""
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip()
    return v if v != "" else default


def _env_bool(name: str, default: bool = False) -> bool:
    v = _env(name)
    if v is None:
        return default
    return v.lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    v = _env(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _env_list(name: str, default: Optional[List[str]] = None) -> List[str]:
    """
    Accepts:
      - JSON list: '["https://a.com","https://b.com"]'
      - CSV string: 'https://a.com,https://b.com'
      - single value
    """
    default = default or []
    raw = _env(name)
    if raw is None:
        return list(default)

    raw = raw.strip()
    if raw.startswith("["):
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                out = [str(x).strip() for x in data]
                return [x for x in out if x]
        except Exception:
            return list(default)

    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


@dataclass(slots=True)
class Settings:
    # Core service identity
    APP_MODE: str
    ENVIRONMENT: str
    PROJECT_NAME: str
    RELAY_NAME: str
    BIFL_VERSION: str

    # Runtime / diagnostics
    PYTHON_VERSION: str
    LOG_LEVEL: str
    LOG_FORMAT: str
    LOG_COLOR: bool

    # OpenAI upstream
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str
    OPENAI_ORGANIZATION: Optional[str]
    OPENAI_PROJECT: Optional[str]
    OPENAI_BETA: Optional[str]
    OPENAI_ASSISTANTS_BETA: Optional[str]
    OPENAI_REALTIME_BETA: Optional[str]
    OPENAI_MAX_RETRIES: int

    DEFAULT_MODEL: str
    REALTIME_MODEL: str

    # Relay runtime
    RELAY_HOST: str
    RELAY_PORT: int
    RELAY_TIMEOUT_SECONDS: int
    PROXY_TIMEOUT_SECONDS: int

    # Stream / orchestration
    ENABLE_STREAM: bool
    CHAIN_WAIT_MODE: str

    # Relay auth
    RELAY_AUTH_ENABLED: bool
    RELAY_KEY: Optional[str]
    CHATGPT_ACTIONS_SECRET: Optional[str]
    RELAY_AUTH_TOKEN: Optional[str]

    # CORS
    CORS_ALLOW_ORIGINS: List[str]
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]
    CORS_ALLOW_CREDENTIALS: bool

    # Tools / schema
    TOOLS_MANIFEST: str
    VALIDATION_SCHEMA_PATH: Optional[str]

    # Convenience aliases (snake_case)
    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def project_name(self) -> str:
        return self.PROJECT_NAME

    @property
    def relay_name(self) -> str:
        return self.RELAY_NAME

    @property
    def version(self) -> str:
        return self.BIFL_VERSION

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

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
    def openai_base_url(self) -> str:
        return self.OPENAI_API_BASE

    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @property
    def openai_organization(self) -> Optional[str]:
        return self.OPENAI_ORGANIZATION

    @property
    def openai_project(self) -> Optional[str]:
        return self.OPENAI_PROJECT

    @property
    def openai_beta(self) -> Optional[str]:
        return self.OPENAI_BETA

    @property
    def openai_assistants_beta(self) -> Optional[str]:
        return self.OPENAI_ASSISTANTS_BETA

    @property
    def openai_realtime_beta(self) -> Optional[str]:
        return self.OPENAI_REALTIME_BETA

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def realtime_model(self) -> str:
        return self.REALTIME_MODEL

    @property
    def proxy_timeout_seconds(self) -> int:
        return self.PROXY_TIMEOUT_SECONDS

    @property
    def timeout_seconds(self) -> int:
        # Backward compatible alias
        return self.PROXY_TIMEOUT_SECONDS

    @property
    def max_retries(self) -> int:
        return self.OPENAI_MAX_RETRIES


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_mode = _env("APP_MODE", "development") or "development"
    environment = _env("ENVIRONMENT", app_mode) or app_mode

    project_name = _env("PROJECT_NAME", "chatgpt-team-relay") or "chatgpt-team-relay"
    relay_name = _env("RELAY_NAME", "ChatGPT Team Relay") or "ChatGPT Team Relay"
    bifl_version = _env("BIFL_VERSION", "local-dev") or "local-dev"

    python_version = _env("PYTHON_VERSION", platform.python_version()) or platform.python_version()
    log_level = _env("LOG_LEVEL", _env("LOGLEVEL", "INFO") or "INFO") or "INFO"
    log_format = _env("LOG_FORMAT", "plain") or "plain"
    log_color = _env_bool("LOG_COLOR", False)

    openai_api_base = _env("OPENAI_API_BASE", "https://api.openai.com/v1") or "https://api.openai.com/v1"
    # Allow empty key at import-time; enforce on upstream call sites.
    openai_api_key = _env("OPENAI_API_KEY", "") or ""
    openai_org = _env("OPENAI_ORGANIZATION", _env("OPENAI_ORG", None))
    openai_project = _env("OPENAI_PROJECT", None)
    openai_beta = _env("OPENAI_BETA", None)
    openai_assistants_beta = _env("OPENAI_ASSISTANTS_BETA", None)
    openai_realtime_beta = _env("OPENAI_REALTIME_BETA", None)
    openai_max_retries = _env_int("OPENAI_MAX_RETRIES", 3)

    default_model = _env("DEFAULT_MODEL", "gpt-5.1") or "gpt-5.1"
    realtime_model = _env("REALTIME_MODEL", "gpt-realtime") or "gpt-realtime"

    relay_host = _env("RELAY_HOST", "0.0.0.0") or "0.0.0.0"
    relay_port = _env_int("RELAY_PORT", 8000)
    relay_timeout_seconds = _env_int("RELAY_TIMEOUT_SECONDS", _env_int("RELAY_TIMEOUT", 90))
    proxy_timeout_seconds = _env_int("PROXY_TIMEOUT_SECONDS", _env_int("PROXY_TIMEOUT", 90))

    enable_stream = _env_bool("ENABLE_STREAM", True)
    chain_wait_mode = _env("CHAIN_WAIT_MODE", "auto") or "auto"

    relay_auth_enabled = _env_bool("RELAY_AUTH_ENABLED", True)
    relay_key = _env("RELAY_KEY", None)
    chatgpt_actions_secret = _env("CHATGPT_ACTIONS_SECRET", None)
    relay_auth_token = _env("RELAY_AUTH_TOKEN", None)

    cors_allow_origins = _env_list("CORS_ALLOW_ORIGINS", default=["*"])
    cors_allow_methods = _env_list("CORS_ALLOW_METHODS", default=["*"])
    cors_allow_headers = _env_list("CORS_ALLOW_HEADERS", default=["*"])
    cors_allow_credentials = _env_bool("CORS_ALLOW_CREDENTIALS", False)

    tools_manifest = _env("TOOLS_MANIFEST", "tools_manifest.json") or "tools_manifest.json"
    validation_schema_path = _env("VALIDATION_SCHEMA_PATH", None)

    return Settings(
        APP_MODE=app_mode,
        ENVIRONMENT=environment,
        PROJECT_NAME=project_name,
        RELAY_NAME=relay_name,
        BIFL_VERSION=bifl_version,
        PYTHON_VERSION=python_version,
        LOG_LEVEL=log_level,
        LOG_FORMAT=log_format,
        LOG_COLOR=log_color,
        OPENAI_API_BASE=openai_api_base,
        OPENAI_API_KEY=openai_api_key,
        OPENAI_ORGANIZATION=openai_org,
        OPENAI_PROJECT=openai_project,
        OPENAI_BETA=openai_beta,
        OPENAI_ASSISTANTS_BETA=openai_assistants_beta,
        OPENAI_REALTIME_BETA=openai_realtime_beta,
        OPENAI_MAX_RETRIES=openai_max_retries,
        DEFAULT_MODEL=default_model,
        REALTIME_MODEL=realtime_model,
        RELAY_HOST=relay_host,
        RELAY_PORT=relay_port,
        RELAY_TIMEOUT_SECONDS=relay_timeout_seconds,
        PROXY_TIMEOUT_SECONDS=proxy_timeout_seconds,
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
    )


# Legacy singleton import pattern used across the codebase
settings: Settings = get_settings()
```

## FILE: app/core/http_client.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from __future__ import annotations

import asyncio
import contextvars
from typing import Optional, Tuple, Any, Callable

import httpx
from openai import AsyncOpenAI

from app.core.config import settings

_httpx_client_var: contextvars.ContextVar[
    Optional[Tuple[asyncio.AbstractEventLoop, httpx.AsyncClient]]
] = contextvars.ContextVar("httpx_async_client", default=None)

_openai_client_var: contextvars.ContextVar[
    Optional[Tuple[asyncio.AbstractEventLoop, AsyncOpenAI]]
] = contextvars.ContextVar("openai_async_client", default=None)


def _get_setting(*names: str, default=None):
    for name in names:
        if hasattr(settings, name):
            val = getattr(settings, name)
            if val is not None:
                return val
    return default


def _default_timeout_s() -> float:
    # Support multiple historical config names.
    return float(
        _get_setting(
            "RELAY_TIMEOUT",
            "RELAY_TIMEOUT_S",
            "OPENAI_TIMEOUT",
            "OPENAI_TIMEOUT_S",
            default=60.0,
        )
    )


def get_async_httpx_client(timeout: Optional[float] = None) -> httpx.AsyncClient:
    """
    Canonical shared AsyncClient (per event loop).

    This is the single HTTP connection pool used for all upstream calls.
    """
    loop = asyncio.get_running_loop()
    cached = _httpx_client_var.get()
    if cached and cached[0] is loop:
        return cached[1]

    t = float(timeout) if timeout is not None else _default_timeout_s()

    client = httpx.AsyncClient(
        timeout=httpx.Timeout(t),
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
        follow_redirects=True,
    )
    _httpx_client_var.set((loop, client))
    return client


def get_async_openai_client() -> AsyncOpenAI:
    """
    Canonical shared AsyncOpenAI client (per event loop).

    Uses the canonical HTTPX pool from get_async_httpx_client().
    """
    loop = asyncio.get_running_loop()
    cached = _openai_client_var.get()
    if cached and cached[0] is loop:
        return cached[1]

    api_key = _get_setting("OPENAI_API_KEY", "openai_api_key")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    base_url = _get_setting(
        "OPENAI_BASE_URL",
        "OPENAI_API_BASE",
        "openai_base_url",
        "openai_api_base",
        default="https://api.openai.com/v1",
    )

    organization = _get_setting("OPENAI_ORG", "OPENAI_ORGANIZATION", "openai_organization")
    project = _get_setting("OPENAI_PROJECT", "openai_project")

    # Reuse our HTTPX pool for upstream calls.
    http_client = get_async_httpx_client()

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        organization=organization,
        project=project,
        http_client=http_client,
    )

    _openai_client_var.set((loop, client))
    return client


async def _maybe_close(obj: Any) -> None:
    """
    Best-effort close for objects that may expose:
      - aclose() (async)
      - close() (sync or async)
    """
    if obj is None:
        return

    closer: Optional[Callable[[], Any]] = None
    if hasattr(obj, "aclose") and callable(getattr(obj, "aclose")):
        closer = getattr(obj, "aclose")
    elif hasattr(obj, "close") and callable(getattr(obj, "close")):
        closer = getattr(obj, "close")

    if closer is None:
        return

    try:
        res = closer()
        if asyncio.iscoroutine(res):
            await res
    except Exception:
        # Shutdown should be best-effort; avoid masking the real shutdown path.
        return


async def close_async_clients() -> None:
    """
    FastAPI shutdown hook.

    Closes cached per-event-loop clients created by:
      - get_async_httpx_client()
      - get_async_openai_client()

    Safe to call multiple times.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop: nothing to close safely in this context.
        return

    cached_openai = _openai_client_var.get()
    cached_httpx = _httpx_client_var.get()

    # Close OpenAI client first (it references the HTTP client).
    if cached_openai and cached_openai[0] is loop:
        await _maybe_close(cached_openai[1])
        _openai_client_var.set(None)

    # Close HTTPX pool.
    if cached_httpx and cached_httpx[0] is loop:
        await _maybe_close(cached_httpx[1])
        _httpx_client_var.set(None)


__all__ = [
    "get_async_httpx_client",
    "get_async_openai_client",
    "close_async_clients",
]
```

## FILE: app/core/logging.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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
from app.utils.logger import get_logger


def configure_logging(settings: Any) -> None:
    """
    Initialise relay logging based on environment variables.

    This function calls into :func:`app.utils.logger.get_logger` which will
    configure the root logger exactly once using the environment variables
    ``LOG_LEVEL``, ``LOG_FORMAT``, and ``LOG_COLOR``. It accepts a
    ``settings`` parameter for interface compatibility, but does not use it
    directly.

    Args:
        settings: settings object (unused but required for API compatibility).
    """
    # Ensure that the root logger is configured. The get_logger call sets up
    # formatting and levels on first invocation.
    get_logger("relay")
```

## FILE: app/http_client.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from __future__ import annotations

# Keep legacy imports working without duplicating logic.
from app.core.http_client import (
    get_async_httpx_client,
    get_async_openai_client,
    close_async_clients,
)

__all__ = ["get_async_httpx_client", "get_async_openai_client", "close_async_clients"]
```

## FILE: app/main.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.sse import create_sse_app
from app.core.config import get_settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes
from app.utils.logger import configure_logging


def _get_bool_setting(settings, snake: str, upper: str, default: bool) -> bool:
    if hasattr(settings, snake):
        v = getattr(settings, snake)
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "on"}

    if hasattr(settings, upper):
        v = getattr(settings, upper)
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "on"}

    return default


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    enable_stream = _get_bool_setting(settings, "enable_stream", "ENABLE_STREAM", True)

    app = FastAPI(
        title="ChatGPT Team Relay",
        version=os.getenv("RELAY_VERSION", "0.0.0"),
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    # Orchestrator (logging / request context)
    app.add_middleware(P4OrchestratorMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # IMPORTANT:
    # Always install RelayAuthMiddleware so tests can toggle RELAY_AUTH_ENABLED via monkeypatch
    # even if the app was created while RELAY_AUTH_ENABLED=false.
    #
    # The middleware itself is a no-op when RELAY_AUTH_ENABLED is false.
    app.add_middleware(RelayAuthMiddleware)

    # Routes
    register_routes(app)

    # SSE mounting (non-actions clients)
    if enable_stream:
        app.mount("/v1/responses:stream", create_sse_app())

    return app


app = create_app()
```

## FILE: app/manifests/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/manifests/tools_manifest.json @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/middleware/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
```

## FILE: app/middleware/p4_orchestrator.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/middleware/relay_auth.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
# app/middleware/relay_auth.py

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.authy import check_relay_key
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Exact paths that should always be public
SAFE_EXACT_PATHS = {
    "/",  # root
    "/health",
    "/health/",
    "/v1/health",
    "/v1/health/",
    "/actions/ping",
    "/actions/relay_info",
    "/v1/actions/ping",
    "/v1/actions/relay_info",
}

# Prefixes that should always be public (docs, openapi, assets, etc.)
SAFE_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
    "/favicon",
)


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional shared-secret auth in front of the relay.

    Controlled by env / settings:

      - RELAY_KEY (or legacy RELAY_AUTH_TOKEN)
      - RELAY_AUTH_ENABLED (bool)

    Behavior:

      - Health + docs + actions ping/info are always public.
      - Non-/v1/ paths remain public.
      - /v1/* paths are protected when RELAY_AUTH_ENABLED is True.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path

        # Public routes
        if path in SAFE_EXACT_PATHS or path.startswith(SAFE_PREFIXES):
            return await call_next(request)

        # Only protect OpenAI-style API paths under /v1
        if not path.startswith("/v1/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        x_relay_key = request.headers.get("X-Relay-Key")

        try:
            # Will no-op if RELAY_AUTH_ENABLED is False
            check_relay_key(auth_header=auth_header, x_relay_key=x_relay_key)
        except HTTPException as exc:
            # DO NOT let this bubble out as an exception to httpx;
            # convert to a normal JSON error response.
            logger.warning(
                "Relay auth failed",
                extra={"path": path, "method": request.method, "detail": exc.detail},
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=getattr(exc, "headers", None) or {},
            )

        # Auth OK (or disabled)
        return await call_next(request)
```

## FILE: app/middleware/validation.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/models/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from .error import ErrorDetail, ErrorResponse

__all__ = ["ErrorDetail", "ErrorResponse"]
```

## FILE: app/models/error.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/routes/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
# app/routes/__init__.py

from .register_routes import register_routes

__all__ = ["register_routes"]
```

## FILE: app/routes/actions.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
# app/routes/actions.py

from __future__ import annotations

from fastapi import APIRouter

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
```

## FILE: app/routes/batches.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/routes/containers.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/routes/conversations.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/routes/embeddings.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/routes/files.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["files"])


@router.get("/files")
async def list_files(request: Request) -> Response:
    """
    GET /v1/files
    Upstream: list files
    """
    logger.info("→ [files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/files")
async def create_file(request: Request) -> Response:
    """
    POST /v1/files
    Upstream expects multipart/form-data (file + purpose).
    We forward as-is.
    """
    logger.info("→ [files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}
    Upstream: retrieve file metadata
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    """
    DELETE /v1/files/{file_id}
    Upstream: delete file
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.get("/files/{file_id}/content")
async def retrieve_file_content_get(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}/content
    Upstream: retrieve file content (binary)
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.head("/files/{file_id}/content", include_in_schema=False)
async def retrieve_file_content_head(file_id: str, request: Request) -> Response:
    """
    HEAD /v1/files/{file_id}/content

    HEAD is useful for clients, but it is not required for Actions/docs.
    We exclude it from OpenAPI to avoid duplicate operationId warnings.
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.api_route(
    "/files/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def files_passthrough(path: str, request: Request) -> Response:
    """
    Catch-all passthrough for future /v1/files/* endpoints.

    Kept out of OpenAPI to avoid operationId collisions and to keep
    the schema Actions-friendly.
    """
    logger.info("→ [files/*] %s %s (subpath=%s)", request.method, request.url.path, path)
    return await forward_openai_request(request)
```

## FILE: app/routes/health.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])

_START_TIME = time.time()


def _health_payload() -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    return {
        "object": "health",
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "default_model": settings.DEFAULT_MODEL,
        "timestamp": now.isoformat(),
        # Nested structures expected by tests
        "relay": {
            "name": settings.RELAY_NAME,
            "app_mode": settings.APP_MODE,
            "auth_enabled": bool(getattr(settings, "RELAY_AUTH_ENABLED", False)),
        },
        "openai": {
            "base_url": settings.OPENAI_BASE_URL,
        },
        "meta": {
            "uptime_seconds": round(time.time() - _START_TIME, 3),
        },
    }


@router.get("/", summary="Health check")
async def root_ping() -> Dict[str, Any]:
    return _health_payload()


@router.get("/health", summary="Health check")
async def health() -> Dict[str, Any]:
    return _health_payload()


@router.get("/v1/health", summary="Health check")
async def v1_health() -> Dict[str, Any]:
    return _health_payload()
```

## FILE: app/routes/images.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from fastapi import APIRouter, Request
from starlette.responses import Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["images"])


@router.post("/images", summary="Create image generation")
@router.post("/images/generations", summary="Create image generation (alias)")
async def create_image(request: Request) -> Response:
    logger.info("→ [images] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/edits", summary="Edit an image (multipart)")
async def edit_image(request: Request) -> Response:
    logger.info("→ [images] %s %s (edits)", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/variations", summary="Create image variations (multipart)")
async def variations_image(request: Request) -> Response:
    logger.info("→ [images] %s %s (variations)", request.method, request.url.path)
    return await forward_openai_request(request)
```

## FILE: app/routes/models.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/routes/proxy.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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
    Action-friendly proxy envelope (Option A).

    NOTE:
    - We intentionally do NOT use a field named `json`, because it shadows
      BaseModel.json() and triggers Pydantic warnings.
    - For backward compatibility, we still ACCEPT an input key named "json"
      as an alias to `body`.
    """

    model_config = ConfigDict(extra="forbid")

    method: str = Field(..., description="HTTP method: GET, POST, PUT, PATCH, DELETE")
    path: str = Field(..., description="Upstream OpenAI path, e.g. /v1/responses")

    # Accept multiple common spellings (client convenience).
    query: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices("query", "params", "query_params"),
        description="Query parameters (object/dict)",
    )

    # Back-compat: accept {"json": {...}} from older clients/examples
    body: Optional[Any] = Field(
        default=None,
        validation_alias=AliasChoices("body", "json", "json_body"),
        description="JSON body for POST/PUT/PATCH requests",
    )

    @model_validator(mode="after")
    def _avoid_empty_json_body_parse_errors(self) -> "ProxyRequest":
        """
        Some clients omit the body entirely for POST-like methods.
        Defaulting to {} gives a consistent upstream behavior (400 w/ details)
        instead of 'empty body' edge cases.
        """
        m = (self.method or "").strip().upper()
        if m in {"POST", "PUT", "PATCH"} and self.body is None:
            self.body = {}
        return self


_ALLOWED_METHODS: Set[str] = {"GET", "POST", "PUT", "PATCH", "DELETE"}

# Block higher-risk or non-Action-friendly families by prefix.
_BLOCKED_PREFIXES: Tuple[str, ...] = (
    "/v1/admin",
    "/v1/webhooks",
    "/v1/moderations",
    "/v1/realtime",   # websocket family (not Actions-friendly)
    "/v1/uploads",    # multipart/resumable
    "/v1/audio",      # often multipart/binary
)

# Block direct recursion and local-only helpers
_BLOCKED_PATHS: Set[str] = {
    "/v1/proxy",
    "/v1/responses:stream",
}

# Block binary-ish suffixes (Actions are JSON-first)
_BLOCKED_SUFFIXES: Tuple[str, ...] = (
    "/content",
    "/results",
)

# Multipart endpoints that should not be routed via JSON envelope
_BLOCKED_METHOD_PATH_REGEX: Set[Tuple[str, re.Pattern[str]]] = {
    ("POST", re.compile(r"^/v1/files$")),
    ("POST", re.compile(r"^/v1/images/(edits|variations)$")),
    ("POST", re.compile(r"^/v1/videos$")),  # per API ref, create video is multipart/form-data
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
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/search$")),

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
    ({"GET"}, re.compile(r"^/v1/conversations/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/conversations/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/conversations/[^/]+$")),

    # ---- Files (JSON metadata only; content is binary; create is multipart) ----
    ({"GET"}, re.compile(r"^/v1/files$")),
    ({"GET"}, re.compile(r"^/v1/files/[A-Za-z0-9_-]+$")),
    ({"DELETE"}, re.compile(r"^/v1/files/[A-Za-z0-9_-]+$")),
)


def _normalize_path(path: str) -> str:
    p = (path or "").strip()

    if not p:
        raise HTTPException(status_code=400, detail="path is required")

    # Disallow full URLs; only allow API paths.
    if "://" in p or p.lower().startswith("http"):
        raise HTTPException(status_code=400, detail="path must be an OpenAI API path, not a URL")

    # Disallow embedded query strings (use `query` field).
    if "?" in p:
        raise HTTPException(status_code=400, detail="path must not include '?'; use `query` field")

    if not p.startswith("/"):
        p = "/" + p

    # Ensure /v1 prefix
    if p.startswith("/v1"):
        normalized = p
    elif p.startswith("v1/"):
        normalized = "/" + p
    else:
        normalized = "/v1" + p

    # Collapse accidental double slashes
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    return normalized


def _blocked_reason(method: str, path: str, body: Any) -> Optional[str]:
    # No streaming via proxy envelope
    if isinstance(body, dict) and body.get("stream") is True:
        return "stream=true is not allowed via /v1/proxy (use explicit streaming route)"

    # Block weird colon paths like /v1/responses:stream
    if ":" in path:
        return "':' paths are not allowed via /v1/proxy"

    # Basic traversal guards
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

## FILE: app/routes/realtime.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
# app/routes/realtime.py

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from websockets import connect as ws_connect  # type: ignore
from websockets.exceptions import ConnectionClosed  # type: ignore

from app.utils.logger import relay_log as logger

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA", "realtime=v1")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
DEFAULT_REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-4.1-mini")

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


async def _post_realtime_sessions(
    request: Request,
    body: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """
    Helper for POST /v1/realtime/sessions
    """
    url = f"{OPENAI_API_BASE}/v1/realtime/sessions"
    headers = _build_headers(request)
    timeout = httpx.Timeout(PROXY_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, headers=headers, json=body or {})
        except httpx.RequestError as exc:
            logger.error("Error calling OpenAI Realtime sessions: %r", exc)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": "Error calling OpenAI Realtime sessions",
                        "type": "server_error",
                        "code": "upstream_request_error",
                        "extra": {"exception": str(exc)},
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
        payload = await request.json()
    except Exception:
        payload = {}

    if not isinstance(payload, dict):
        payload = {}

    payload.setdefault("model", DEFAULT_REALTIME_MODEL)

    status_code, data = await _post_realtime_sessions(request, payload)
    return JSONResponse(status_code=status_code, content=data)


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
      ws(s)://relay-host/v1/realtime/ws?model=.&session_id=.

    Relay connects to:
      wss://api.openai.com/v1/realtime?model=.&session_id=.
    """
    await websocket.accept(subprotocol="openai-realtime-v1")

    model = websocket.query_params.get("model") or DEFAULT_REALTIME_MODEL
    session_id = websocket.query_params.get("session_id")

    ws_base = _build_ws_base()
    url = f"{ws_base}/v1/realtime?model={model}"
    if session_id:
        url += f"&session_id={session_id}"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": OPENAI_REALTIME_BETA,
    }

    try:
        async with ws_connect(
            url,
            extra_headers=headers,
            subprotocols=["openai-realtime-v1"],
        ) as upstream_ws:

            async def _client_to_openai() -> None:
                try:
                    while True:
                        msg = await websocket.receive()
                        if msg["type"] == "websocket.disconnect":
                            await upstream_ws.close()
                            break
                        if msg.get("text") is not None:
                            await upstream_ws.send(msg["text"])
                        elif msg.get("bytes") is not None:
                            await upstream_ws.send(msg["bytes"])
                except WebSocketDisconnect:
                    await upstream_ws.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Client->OpenAI WS error: %r", exc)
                    await upstream_ws.close()

            async def _openai_to_client() -> None:
                try:
                    async for message in upstream_ws:
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except ConnectionClosed:
                    await websocket.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("OpenAI->Client WS error: %r", exc)
                    await websocket.close()

            await asyncio.gather(_client_to_openai(), _openai_to_client())

    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to establish WS to OpenAI: %r", exc)
        await websocket.close()
```

## FILE: app/routes/register_routes.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

    # Health is special: exposes both `/health` and `/v1/health`
    app.include_router(health.router)

    # Relay diagnostics / metadata for Actions
    app.include_router(actions.router)

    # Core OpenAI resource families
    app.include_router(responses.router)  # /v1/responses
    app.include_router(embeddings.router)  # /v1/embeddings
    app.include_router(images.router)  # /v1/images
    app.include_router(videos.router)  # /v1/videos
    app.include_router(models.router)  # /v1/models (local stub)

    # Files & uploads (multipart, binary content)
    app.include_router(files.router)  # /v1/files
    app.include_router(uploads.router)  # /v1/uploads
    app.include_router(vector_stores.router)  # /v1/vector_stores (+ /vector_stores)

    # Higher-level surfaces
    app.include_router(conversations.router)  # /v1/conversations
    app.include_router(containers.router)  # /v1/containers
    app.include_router(batches.router)  # /v1/batches
    app.include_router(realtime.router)  # /v1/realtime (HTTP + WS)

    # Generic allowlisted proxy LAST
    app.include_router(proxy.router)  # /v1/proxy


def register_all_routes(app: _RouterLike) -> None:
    """Backwards compatibility alias (older main.py imports)."""
    register_routes(app)
```

## FILE: app/routes/responses.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.api.forward_openai import (
    build_upstream_url,
    forward_openai_request,
    forward_responses_create,
)
from app.api.sse import create_sse_stream
from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client

router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    POST /v1/responses
    - Supports JSON payload
    - If payload has {"stream": true}, we stream SSE from upstream.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # If stream requested, proxy SSE stream directly.
    if body.get("stream") is True:
        settings = get_settings()
        url = build_upstream_url("/v1/responses")

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        if settings.openai_organization:
            headers["OpenAI-Organization"] = settings.openai_organization
        if settings.openai_project:
            headers["OpenAI-Project"] = settings.openai_project
        if settings.openai_beta:
            headers["OpenAI-Beta"] = settings.openai_beta

        data = json.dumps(body).encode("utf-8")
        client = get_async_httpx_client()

        async def event_generator():
            async with client.stream(
                "POST",
                url,
                headers=headers,
                content=data,
                timeout=settings.proxy_timeout_seconds,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        yield line + "\n"

        return StreamingResponse(
            create_sse_stream(event_generator()),
            media_type="text/event-stream",
        )

    # Non-streaming: use SDK (typed) and return JSON.
    result = await forward_responses_create(body)
    return Response(
        content=json.dumps(result),
        media_type="application/json",
    )


@router.post("/responses/compact")
async def create_response_compact(request: Request) -> Response:
    """
    POST /v1/responses/compact
    - convenience wrapper that can keep payload minimal on the client side
    """
    body = await request.json()
    body["metadata"] = body.get("metadata", {})
    body["metadata"]["compact"] = True
    result = await forward_responses_create(body)
    return Response(
        content=json.dumps(result),
        media_type="application/json",
    )


# --- Missing lifecycle endpoints (now added) ---


@router.get("/responses/{response_id}")
async def get_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.delete("/responses/{response_id}")
async def delete_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/responses/{response_id}/input_items")
async def get_response_input_items(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/responses/input_tokens")
async def get_input_token_counts(request: Request) -> Response:
    """
    POST /v1/responses/input_tokens
    (This is a top-level endpoint in the OpenAI API reference.)
    """
    return await forward_openai_request(request)


# Catch-all passthrough for future /v1/responses/* subroutes.
@router.api_route(
    "/responses/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def responses_passthrough(path: str, request: Request) -> Response:
    return await forward_openai_request(request)


# --- Simple SSE helper endpoint used by some clients/tests ---


@router.get("/responses:stream")
async def responses_stream() -> Response:
    """
    Deprecated-ish helper. Kept for compatibility.
    """
    async def gen():
        for i in range(3):
            yield f"data: ping {i}\n\n"
            await asyncio.sleep(0.1)

    return StreamingResponse(gen(), media_type="text/event-stream")
```

## FILE: app/routes/uploads.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
# app/routes/uploads.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["uploads"])


@router.post("/uploads")
async def create_upload(request: Request) -> Response:
    """
    POST /v1/uploads

    Upstream: Creates an intermediate Upload; once completed, it yields a File.
    (OpenAI API Reference: Uploads)
    """
    logger.info("→ [uploads] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/parts")
async def add_upload_part(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/parts

    Upstream expects multipart/form-data with a required 'data' file field.
    We forward as-is.
    """
    logger.info("→ [uploads] %s %s (upload_id=%s)", request.method, request.url.path, upload_id)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/complete")
async def complete_upload(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/complete

    Upstream expects JSON body:
      {"part_ids": ["part_...","part_..."], "md5": "..."}  # md5 optional
    """
    logger.info("→ [uploads] %s %s (complete upload_id=%s)", request.method, request.url.path, upload_id)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/cancel")
async def cancel_upload(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/cancel
    """
    logger.info("→ [uploads] %s %s (cancel upload_id=%s)", request.method, request.url.path, upload_id)
    return await forward_openai_request(request)


@router.api_route(
    "/uploads/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def uploads_passthrough(path: str, request: Request) -> Response:
    """
    Catch-all passthrough for future /v1/uploads/* endpoints.
    """
    logger.info("→ [uploads/*] %s %s (subpath=%s)", request.method, request.url.path, path)
    return await forward_openai_request(request)
```

## FILE: app/routes/vector_stores.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/routes/videos.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_method_path, forward_openai_request
from app.utils.logger import info

router = APIRouter(prefix="/v1", tags=["videos"])


# --- Canonical Videos API (per OpenAI API reference) ---
#
# POST   /v1/videos                       -> create a video generation job (may be multipart)
# POST   /v1/videos/{video_id}/remix       -> remix an existing video
# GET    /v1/videos                       -> list videos
# GET    /v1/videos/{video_id}            -> retrieve a video job
# DELETE /v1/videos/{video_id}            -> delete a video job
# GET    /v1/videos/{video_id}/content    -> download generated content (binary)
#
# We implement the main paths explicitly (for clean OpenAPI + clarity), and keep a
# hidden catch-all for forward-compat endpoints that may appear later.


@router.post("/videos")
async def create_video(request: Request):
    """Create a new video generation job (JSON or multipart/form-data)."""
    info("→ [videos.create] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/videos/generations", deprecated=True)
async def create_video_legacy_generations(request: Request):
    """Legacy alias: historically `/v1/videos/generations` in older relays.

    The current OpenAI API uses `POST /v1/videos`. We forward this endpoint to
    the canonical path for compatibility.
    """
    info("→ [videos.legacy_generations] %s %s", request.method, request.url.path)
    return await forward_openai_method_path("POST", "/v1/videos", request)


@router.post("/videos/{video_id}/remix")
async def remix_video(video_id: str, request: Request):
    """Create a remix of an existing video job."""
    info("→ [videos.remix] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos")
async def list_videos(request: Request):
    """List video jobs."""
    info("→ [videos.list] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}")
async def retrieve_video(video_id: str, request: Request):
    """Retrieve a single video job."""
    info("→ [videos.retrieve] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str, request: Request):
    """Delete a single video job."""
    info("→ [videos.delete] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}/content")
async def download_video_content(video_id: str, request: Request):
    """Download generated content (binary) for a video job."""
    info("→ [videos.content] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# Forward-compat / extra endpoints (hidden from OpenAPI schema)
@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "PUT", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def videos_passthrough(path: str, request: Request):
    info("→ [videos/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
```

## FILE: app/utils/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
```

## FILE: app/utils/authy.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
# app/utils/authy.py

from __future__ import annotations

import hmac
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _get_expected_key() -> str:
    """
    Return the configured relay key as a plain string.

    Prefer settings.RELAY_KEY, but keep a fallback to RELAY_AUTH_TOKEN
    for compatibility with older configs.
    """
    if getattr(settings, "RELAY_KEY", None):
        return settings.RELAY_KEY

    # Legacy / fallback name
    token = getattr(settings, "RELAY_AUTH_TOKEN", None)
    return token or ""


def _extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Parse an Authorization header of the form 'Bearer <token>'.

    Returns the token string, or None if the header is missing.

    Raises HTTPException(401) if the header is present but malformed.
    """
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Relay requires 'Bearer' Authorization scheme",
        )

    token = parts[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing relay key",
        )

    return token


def check_relay_key(
    auth_header: Optional[str],
    x_relay_key: Optional[str],
) -> None:
    """
    Validate incoming relay key.

    Priority:
      1. X-Relay-Key header (used by relay_e2e_raw.py / tools)
      2. Authorization: Bearer <token> (used by SDK-style clients)

    If RELAY_AUTH_ENABLED is False, this is a no-op.

    On failure, raises HTTPException(status_code=..., detail="<string>").
    """
    # If auth is disabled, skip entirely
    if not getattr(settings, "RELAY_AUTH_ENABLED", False):
        return

    # Prefer explicit X-Relay-Key when present
    token: Optional[str] = None
    if x_relay_key:
        token = x_relay_key.strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing relay key",
            )
    else:
        # Fall back to Authorization header
        token = _extract_bearer_token(auth_header)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing relay key",
        )

    expected = _get_expected_key().encode("utf-8")
    provided = token.encode("utf-8")

    if not expected:
        # Config bug; log and fail closed
        logger.error(
            "Relay auth misconfigured: RELAY_KEY is empty when auth is enabled",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Relay auth misconfigured",
        )

    if not hmac.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid relay key",
        )
```

## FILE: app/utils/error_handler.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: app/utils/http_client.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from __future__ import annotations

from app.core.http_client import get_async_httpx_client

__all__ = ["get_async_httpx_client"]
```

## FILE: app/utils/logger.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional

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

## FILE: tests/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
```

## FILE: tests/client.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: tests/conftest.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
import os

import httpx
import pytest


@pytest.fixture(scope="session")
def relay_base_url() -> str:
    return os.getenv("RELAY_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def relay_token() -> str:
    return os.getenv("RELAY_TOKEN", "")


@pytest.fixture(scope="session")
async def client(relay_base_url: str, relay_token: str):
    """
    Default integration client.

    Important: The test suite sets relay auth OFF by default so local tests run
    without requiring a key. Individual tests can monkeypatch settings to enable it.
    """
    os.environ.setdefault("RELAY_AUTH_ENABLED", "false")
    os.environ.setdefault("RELAY_KEY", "dummy")

    headers: dict[str, str] = {}
    if relay_token:
        headers["Authorization"] = f"Bearer {relay_token}"

    async with httpx.AsyncClient(
        base_url=relay_base_url,
        headers=headers,
        timeout=60.0,
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
async def async_client(client: httpx.AsyncClient) -> httpx.AsyncClient:
    """
    Alias fixture for tests that expect `async_client` by name.
    """
    return client
```

## FILE: tests/test_extended_routes_smoke_integration.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

    # A minimal valid PNG (1x1) to exercise multipart forwarding without external deps.
    tiny_png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+vmFoAAAAASUVORK5CYII="
    )
    png_bytes = base64.b64decode(tiny_png_b64)

    # IMPORTANT: Do not set Content-Type manually for multipart; requests will set the boundary.
    files = {"image": ("input.png", png_bytes, "image/png")}

    # Use an intentionally invalid model to avoid any billable work; wiring is the goal.
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

## FILE: tests/test_files_and_batches_integration.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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
    return bool(os.getenv(INTEGRATION_ENV_VAR))


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

## FILE: tests/test_images_variations_integration.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: tests/test_local_e2e.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
# tests/test_local_e2e.py
from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import settings

# All tests in this module are async
pytestmark = pytest.mark.asyncio


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


@pytest.mark.integration
async def test_responses_non_streaming_basic(async_client: httpx.AsyncClient) -> None:
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


@pytest.mark.integration
async def test_responses_streaming_sse_basic(async_client: httpx.AsyncClient) -> None:
    """
    Verify that the relay streams SSE events in the same shape as api.openai.com.

    We do not fully parse every event; we just assert that:
      - The HTTP status is 200
      - The SSE stream includes at least one `response.output_text.delta`
      - The SSE stream ends with `response.completed`
    """
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


@pytest.mark.integration
async def test_embeddings_basic(async_client: httpx.AsyncClient) -> None:
    """
    Simple check that the relay can forward /v1/embeddings and the shape matches
    OpenAI's embeddings API.
    """
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

@pytest.mark.integration
async def test_responses_compact_basic(async_client: httpx.AsyncClient) -> None:
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


@pytest.mark.integration
async def test_tools_manifest_has_responses_endpoints(async_client: httpx.AsyncClient) -> None:
    resp = await async_client.get("/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert "/v1/responses" in data["endpoints"]["responses"]
    assert "/v1/responses/compact" in data["endpoints"]["responses_compact"]
```

## FILE: tests/test_relay_auth_guard.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: tests/test_remaining_routes_smoke_integration.py @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: tests/test_success_gates_integration.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
"""
Success gates for the relay (integration).

Gates:
- Gate A: Uploads E2E passes (happy path + cancel path)
- Gate B: SSE smoke passes (streaming content-type + incremental reads)
- Gate C: OpenAPI has no duplicate operationId warnings (validated by uniqueness check)
- Gate D: containers/videos `/content` endpoints validated (no relay 5xx; upstream 4xx is OK)

Requires:
  INTEGRATION_OPENAI_API_KEY=1
Optional env:
  RELAY_BASE_URL (default http://localhost:8000)
  RELAY_TOKEN    (default dummy)
  DEFAULT_MODEL  (default gpt-5.1)
"""

from __future__ import annotations

import os
from collections import Counter
from typing import Any, Dict, List

import pytest
import requests


pytestmark = pytest.mark.integration

RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
RELAY_TOKEN = os.getenv("RELAY_TOKEN", "dummy")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-5.1")

DEFAULT_TIMEOUT_S = float(os.getenv("RELAY_TEST_TIMEOUT_S", "60"))


def _skip_if_no_real_key() -> None:
    # Keep this consistent with existing integration tests.
    if os.getenv("INTEGRATION_OPENAI_API_KEY") != "1":
        pytest.skip("INTEGRATION_OPENAI_API_KEY != 1 (skipping real-API integration tests)")


def _auth_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    headers = {"Authorization": f"Bearer {RELAY_TOKEN}"}
    if extra:
        headers.update(extra)
    return headers


def _must_ok(r: requests.Response, *, hint: str = "") -> None:
    if r.ok:
        return
    # Provide debuggable payload (but keep it bounded).
    body = r.text
    if len(body) > 4000:
        body = body[:4000] + "…(truncated)"
    raise AssertionError(f"{hint}HTTP {r.status_code} {r.reason}: {body}")


# -------------------------
# Gate A: Uploads E2E
# -------------------------

def test_gate_a_uploads_e2e_happy_path_and_cancel_path() -> None:
    """
    Uploads API flow per OpenAI docs:
      1) POST /v1/uploads
      2) POST /v1/uploads/{upload_id}/parts (multipart field name: data)
      3) POST /v1/uploads/{upload_id}/complete (ordered part_ids)
      4) POST /v1/uploads/{upload_id}/cancel (cancel path)
    """
    _skip_if_no_real_key()

    # Happy path: upload a tiny file in a single part, then complete.
    payload = {
        "purpose": "batch",
        "filename": "relay_ping.txt",
        "bytes": 4,
        "mime_type": "text/plain",
        # expires_after optional; keep default behavior.
    }
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/uploads",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Create upload failed. ")
    upload = r.json()
    upload_id = upload.get("id")
    assert isinstance(upload_id, str) and upload_id.startswith("upload_")

    # Add one part (multipart, field name MUST be `data`).
    part_bytes = b"ping"
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/uploads/{upload_id}/parts",
        headers=_auth_headers(),
        files={"data": ("part.bin", part_bytes, "application/octet-stream")},
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Add upload part failed. ")
    part_obj = r.json()
    part_id = part_obj.get("id")
    assert isinstance(part_id, str) and part_id.startswith("part_")

    # Complete (md5 is optional per docs; omit to avoid format mismatch).
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/uploads/{upload_id}/complete",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={"part_ids": [part_id]},
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Complete upload failed. ")
    completed = r.json()
    assert completed.get("status") == "completed"
    file_obj = completed.get("file")
    assert isinstance(file_obj, dict)
    file_id = file_obj.get("id")
    assert isinstance(file_id, str) and file_id.startswith("file-")

    # Cancel path: create a second upload then cancel immediately.
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/uploads",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json={
            "purpose": "batch",
            "filename": "relay_cancel.txt",
            "bytes": 1,
            "mime_type": "text/plain",
        },
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Create upload (cancel path) failed. ")
    cancel_upload_id = r.json().get("id")
    assert isinstance(cancel_upload_id, str) and cancel_upload_id.startswith("upload_")

    r = requests.post(
        f"{RELAY_BASE_URL}/v1/uploads/{cancel_upload_id}/cancel",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _must_ok(r, hint="Cancel upload failed. ")
    cancelled = r.json()
    assert cancelled.get("status") == "cancelled"


# -------------------------
# Gate B: SSE smoke
# -------------------------

def test_gate_b_sse_smoke_streaming_content_type_and_incremental_reads() -> None:
    """
    Smoke-test the relay's SSE endpoint:
      - Content-Type includes text/event-stream
      - We receive multiple chunks/lines (incremental)
      - The streamed content contains the expected token ("pong")
    """
    _skip_if_no_real_key()

    with requests.post(
        f"{RELAY_BASE_URL}/v1/responses:stream",
        headers=_auth_headers(
            {
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            }
        ),
        json={"model": DEFAULT_MODEL, "input": "Return exactly: pong"},
        stream=True,
        timeout=DEFAULT_TIMEOUT_S,
    ) as r:
        _must_ok(r, hint="SSE request failed. ")
        ct = (r.headers.get("content-type") or "").lower()
        assert "text/event-stream" in ct

        lines: List[str] = []
        # Read up to N lines to avoid hanging if upstream stalls.
        for line in r.iter_lines(decode_unicode=True):
            if line is None:
                continue
            if line == "":
                continue
            lines.append(line)
            # Exit early once we see the expected token.
            if "pong" in line:
                break
            if len(lines) >= 200:
                break

        # Must have multiple lines to indicate incremental streaming.
        assert len(lines) >= 3, f"Expected multiple SSE lines, got {len(lines)} lines: {lines[:10]}"
        assert any("pong" in ln for ln in lines), f"Did not find 'pong' in SSE lines: {lines[:20]}"


# -------------------------
# Gate C: OpenAPI operationIds are unique
# -------------------------

def test_gate_c_openapi_has_no_duplicate_operation_ids() -> None:
    """
    FastAPI emits runtime warnings for duplicated operationIds.
    We validate the OpenAPI JSON that the relay serves has unique operationId values.
    """
    r = requests.get(f"{RELAY_BASE_URL}/openapi.json", timeout=DEFAULT_TIMEOUT_S)
    _must_ok(r, hint="GET /openapi.json failed. ")
    spec = r.json()

    op_ids: List[str] = []
    paths: Dict[str, Any] = spec.get("paths", {}) or {}
    for _path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for _method, op in methods.items():
            if not isinstance(op, dict):
                continue
            op_id = op.get("operationId")
            if isinstance(op_id, str) and op_id.strip():
                op_ids.append(op_id.strip())

    counts = Counter(op_ids)
    dups = sorted([op_id for op_id, n in counts.items() if n > 1])

    assert not dups, f"Duplicate operationId values found: {dups}"


# -------------------------
# Gate D: containers/videos content endpoints are wired
# -------------------------

def _assert_not_5xx(r: requests.Response, *, label: str) -> None:
    assert r.status_code < 500, f"{label} returned {r.status_code} (expected <500). Body: {r.text[:800]}"


def test_gate_d_containers_and_videos_content_endpoints_no_relay_5xx() -> None:
    """
    Without creating real container/video objects (cost/complexity),
    we validate that:
      - the endpoints exist and route to upstream
      - relay does not raise 5xx due to wiring/header bugs
    """
    # Containers file content (likely 404/400 from upstream due to dummy ids)
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/containers/cntr_dummy/files/file_dummy/content",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _assert_not_5xx(r, label="containers content")

    # Videos content (likely 404/400 from upstream due to dummy id)
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/videos/vid_dummy/content",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _assert_not_5xx(r, label="videos content")
```

## BASELINE (static/)

## FILE: static/.well-known/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
```

## FILE: static/.well-known/ai-plugin.json @ 834ed1053166c0c0551d2195ee113f003ee84712
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

## FILE: schemas/__init__.py @ 834ed1053166c0c0551d2195ee113f003ee84712
```
```

## FILE: schemas/openapi.yaml @ 834ed1053166c0c0551d2195ee113f003ee84712
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

components: {}
```

## BASELINE (src/)

## BASELINE (scripts/src/)

