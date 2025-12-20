#!/usr/bin/env bash
set -euo pipefail

# chatgpt_sync.sh (v4.1 - explicit allowlist + UTF-16/UTF-32 text conversion)
#
# Purpose:
#   Generate a Markdown artifact that ChatGPT can ingest to get FULL current code/config text
#   for your repo, while avoiding secrets and noisy/generated artifacts.
#
# Default INCLUDE scope (customizable via flags):
#   - Root files (text): pyproject.toml, project-tree.md, openai_models_2025-11.csv,
#                        requirements.txt, render.yaml, pytest.ini, chatgpt_sync.sh
#   - Directories (recursive): app/, tests/, static/, schemas/
#
# Always EXCLUDED:
#   - Secrets: .env, .env.*, *.env, keys/certs
#   - Caches/artifacts: __pycache__/, *.pyc, venvs, logs
#   - Runtime state: data/ (and *.db / *.sqlite*)
#   - Generated outputs: chatgpt_sync.md, chatgpt_baseline.md, chatgpt_changes.md
#
# Modes:
#   baseline  -> embeds baseline content from a base commit (merge-base of HEAD and --base ref)
#   changes   -> shows diff vs base commit AND embeds CURRENT (worktree) content of changed files
#                (includes uncommitted edits)
#
# NOTE ABOUT "Not embedded (binary/large)":
#   This script treats any file containing NUL bytes as "binary".
#   Some Windows editors may save text files as UTF-16/UTF-32, which contains NUL bytes.
#   v4.1 attempts to detect UTF-16/UTF-32 BOM and convert to UTF-8 before embedding.
#
# Usage:
#   ./chatgpt_sync.sh baseline --base origin/main --out chatgpt_baseline.md --max-bytes 2000000
#   ./chatgpt_sync.sh changes  --base origin/main --out chatgpt_changes.md  --max-bytes 2000000
#
# Optional:
#   --dir <path>   repeatable; if specified, replaces default dirs
#   --root <file>  repeatable; if specified, replaces default root files
#   --no-tree      omit file trees
#
# Notes:
#   - Binary-ish files (pdf/db/images/pyc/etc.) are not embedded; we record size + sha256 instead.

MODE="${1:-}"
shift || true

BASE_REV="origin/main"
OUT_FILE="chatgpt_sync.md"
MAX_BYTES="2000000"
EMIT_TREE="true"

# Defaults (override by passing --dir/--root)
DIRS_DEFAULT=( "app" "tests" "static" "schemas" )
ROOT_FILES_DEFAULT=( "pyproject.toml" "project-tree.md" "openai_models_2025-11.csv" "requirements.txt" "render.yaml" "pytest.ini" "chatgpt_sync.sh" )

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

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "Not in a git repo"
cd "$REPO_ROOT"

git fetch -q origin >/dev/null 2>&1 || true

BASE_COMMIT="$(git merge-base HEAD "$BASE_REV" 2>/dev/null || true)"
[[ -n "$BASE_COMMIT" ]] || die "Could not compute merge-base with base '$BASE_REV' (invalid ref?)"

NOW_ISO="$(date -Iseconds)"

# If user didn't pass --dir, use defaults
if [[ "${#DIRS[@]}" -eq 0 ]]; then
  DIRS=( "${DIRS_DEFAULT[@]}" )
fi

# If user didn't pass --root, use defaults
if [[ "${#ROOT_FILES[@]}" -eq 0 ]]; then
  ROOT_FILES=( "${ROOT_FILES_DEFAULT[@]}" )
fi

# ---- denylist: never embed these paths ----
is_denied_path() {
  local p="$1"
  case "$p" in
    # secrets/env/keys
    .env|.env.*|*.env|*.key|*.pem|*.p12|*.pfx|*.crt|*.cer|*.der|*.jks|*.kdbx) return 0 ;;
    # venv/caches/logs
    .venv/*|venv/*|__pycache__/*|*.pyc|*.pyo|*.log|.pytest_cache/*|.mypy_cache/*|.ruff_cache/*) return 0 ;;
    # runtime state
    data/*|data) return 0 ;;
    # generated artifacts (avoid recursion)
    chatgpt_sync.md|chatgpt_baseline.md|chatgpt_changes.md) return 0 ;;
  esac
  return 1
}

# ---- binary-ish extensions: record hash + size, but do not embed content ----
is_binary_ext() {
  local p="$1"
  case "$p" in
    *.pdf|*.png|*.jpg|*.jpeg|*.gif|*.zip|*.tar|*.gz|*.7z|*.whl|*.so|*.dylib|*.exe|*.db|*.sqlite|*.sqlite3|*.db-wal|*.db-shm|*.pyc) return 0 ;;
  esac
  return 1
}

is_binary_stream() { LC_ALL=C grep -q $'\x00' && return 0 || return 1; }

# Try to convert UTF-16/UTF-32-with-BOM to UTF-8 so the content can be embedded.
# Returns 0 if file is now safe-to-embed as text (no NUL bytes), else returns 1.
maybe_convert_to_utf8_inplace() {
  local f="$1"

  # If already looks like normal text, keep it.
  if ! is_binary_stream <"$f"; then
    return 0
  fi

  # No iconv? can't convert.
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
    *)
      # Unknown encoding with NULs: do not guess.
      return 1
      ;;
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
  if is_binary_stream <"$f"; then
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

  # If it's UTF-16/32 text, convert so we can embed it.
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

  # Worktree-inclusive diff (includes uncommitted edits)
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
