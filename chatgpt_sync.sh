#!/usr/bin/env bash
set -euo pipefail

# chatgpt_sync.sh (v2)
#
# Goal (for ChatGPT context):
#   - ALWAYS include selected repo-root files:
#       project-tree.md, pytest.ini, render.yaml, requirements.txt
#     (these are repo-root, same level as ./app)
#   - Include ALL files under a target directory (default: app/)
#   - Optionally include ALL tracked repo-root files (not directories), excluding secrets
#
# Usage:
#   ./chatgpt_sync.sh baseline [--base origin/main] [--dir app] [--out chatgpt_baseline.md] [--max-bytes 2000000] [--include-root-all]
#   ./chatgpt_sync.sh changes  [--base origin/main] [--dir app] [--out chatgpt_changes.md]  [--max-bytes 2000000] [--include-root-all]
#
# Flags:
#   --base <rev>           Base revision to compare against (default: origin/main)
#   --dir <path>           Target directory to sync (default: app)
#   --out <file>           Output markdown file (default: chatgpt_sync.md)
#   --max-bytes <n>        Max bytes per file to embed (default: 200000)
#   --include-bashrc       Append ~/.bashrc content to the artifact
#   --include-root-all     Also include ALL tracked repo-root files (non-directories), excluding secrets
#   --no-tree              Disable emitting TREE sections

MODE="${1:-}"
shift || true

BASE_REV="origin/main"
TARGET_DIR="app"
OUT_FILE="chatgpt_sync.md"
INCLUDE_BASHRC="false"
INCLUDE_ROOT_ALL="false"
MAX_BYTES="200000"
EMIT_TREE="true"

# Always-include repo-root files (same level as ./app)
ROOT_PINNED_FILES=( "project-tree.md" "pytest.ini" "render.yaml" "requirements.txt" )

die() { echo "ERROR: $*" >&2; exit 1; }

usage() {
  cat >&2 <<'EOF'
Usage:
  ./chatgpt_sync.sh baseline|changes [flags]

Flags:
  --base <rev>             Base revision (default: origin/main)
  --base-ref <rev>         Alias for --base
  --dir <path>             Target directory to sync (default: app)
  --out <file>             Output markdown file (default: chatgpt_sync.md)
  --include-bashrc         Include $HOME/.bashrc content
  --include-root-all       Include ALL tracked repo-root files (non-directories), excluding secrets
  --max-bytes <n>          Max bytes per file to embed (default: 200000)
  --no-tree                Do not emit TREE sections
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base|--base-ref) BASE_REV="${2:-}"; shift 2 ;;
    --dir) TARGET_DIR="${2:-}"; shift 2 ;;
    --out) OUT_FILE="${2:-}"; shift 2 ;;
    --include-bashrc) INCLUDE_BASHRC="true"; shift 1 ;;
    --include-root-all) INCLUDE_ROOT_ALL="true"; shift 1 ;;
    --max-bytes) MAX_BYTES="${2:-}"; shift 2 ;;
    --no-tree) EMIT_TREE="false"; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

[[ "$MODE" == "baseline" || "$MODE" == "changes" ]] || { usage; die "First arg must be baseline or changes"; }
command -v git >/dev/null 2>&1 || die "git is required"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "Not in a git repo"
cd "$REPO_ROOT"

# Best-effort fetch (ignore if offline)
git fetch -q origin >/dev/null 2>&1 || true

BASE_COMMIT="$(git merge-base HEAD "$BASE_REV" 2>/dev/null || true)"
[[ -n "$BASE_COMMIT" ]] || die "Could not compute merge-base with base '$BASE_REV' (invalid ref?)"

NOW_ISO="$(date -Iseconds)"
REL_TARGET_DIR="${TARGET_DIR%/}"

# ---- Secret / noise denylist ----
# If a file matches these patterns, it will never be embedded even if tracked.
is_denied_path() {
  local p="$1"
  case "$p" in
    # secrets / env
    .env|.env.*|*.env|*.key|*.pem|*.p12|*.pfx|*.crt|*.cer|*.der|*.jks|*.kdbx|*.sqlite|*.db|*.db-wal|*.db-shm
      ) return 0 ;;
    # big binary-ish / artifacts
    *.pdf|*.png|*.jpg|*.jpeg|*.gif|*.zip|*.tar|*.gz|*.7z|*.whl|*.so|*.dylib|*.exe
      ) return 0 ;;
    # local caches / venv / node
    .venv/*|venv/*|node_modules/*|__pycache__/*|.pytest_cache/*|.mypy_cache/*|.ruff_cache/*
      ) return 0 ;;
    # data directories (adjust if you actually want them)
    data/*|uploads/*|*.egg-info/*
      ) return 0 ;;
  esac
  return 1
}

is_binary_stream() { LC_ALL=C grep -q $'\x00' && return 0 || return 1; }

safe_embed_text() {
  # Args: <label> <bytes> <command...>
  local label="$1"
  local bytes="$2"
  shift 2

  if [[ "$bytes" -gt "$MAX_BYTES" ]]; then
    cat <<EOF
## FILE: ${label}
> Skipped: file size ${bytes} bytes exceeds max ${MAX_BYTES} bytes. Upload separately or raise --max-bytes.
EOF
    return 0
  fi

  local tmp
  tmp="$(mktemp)"
  if ! "$@" >"$tmp" 2>/dev/null; then
    rm -f "$tmp"
    cat <<EOF
## FILE: ${label}
> Skipped: could not read file content.
EOF
    return 0
  fi

  if is_binary_stream <"$tmp"; then
    rm -f "$tmp"
    cat <<EOF
## FILE: ${label}
> Skipped: binary file detected (often UTF-16 or contains NUL bytes).
EOF
    return 0
  fi

  cat <<EOF
## FILE: ${label}
\`\`\`
EOF
  cat "$tmp"
  cat <<'EOF'
```
EOF
  rm -f "$tmp"
}

write_header() {
  cat <<EOF
# ChatGPT Sync
Repo: $(basename "$REPO_ROOT")
Base: ${BASE_REV}
Base commit (merge-base): ${BASE_COMMIT}
Target dir: ${REL_TARGET_DIR}/
Pinned root files: ${ROOT_PINNED_FILES[*]}
Include all root files: ${INCLUDE_ROOT_ALL}
Mode: ${MODE}
Generated: ${NOW_ISO}

EOF
}

# Root-only tracked files (non-recursive)
list_root_files_at_commit() {
  local commit="$1"
  git ls-tree --name-only "$commit" | sed '/^$/d' || true
}

# Recursive tracked files under target dir
list_dir_files_at_commit() {
  local commit="$1"
  git ls-tree -r --name-only "$commit" -- "$REL_TARGET_DIR" || true
}

emit_tree() {
  local commit="$1"

  echo "## TREE (repo root at ${commit})"
  echo '```'
  list_root_files_at_commit "$commit" | sed 's/^/ - /'
  echo '```'
  echo

  echo "## TREE (${REL_TARGET_DIR}/ at ${commit})"
  echo '```'
  list_dir_files_at_commit "$commit" | sed 's/^/ - /'
  echo '```'
  echo
}

embed_root_files_baseline() {
  local commit="$1"

  echo "## BASELINE CONTENT (PINNED ROOT FILES at ${commit})"
  echo

  local f size
  for f in "${ROOT_PINNED_FILES[@]}"; do
    if is_denied_path "$f"; then
      echo "## FILE: ${f} @ ${commit}"
      echo "> Skipped: denied by pattern."
      echo
      continue
    fi

    if git cat-file -e "${commit}:${f}" 2>/dev/null; then
      size="$(git cat-file -s "${commit}:${f}" 2>/dev/null || echo 0)"
      safe_embed_text "${f} @ ${commit}" "$size" git show "${commit}:${f}"
      echo
    else
      echo "## FILE: ${f} @ ${commit}"
      echo "> Missing at ${commit}"
      echo
    fi
  done

  if [[ "$INCLUDE_ROOT_ALL" != "true" ]]; then
    return 0
  fi

  echo "## BASELINE CONTENT (ALL TRACKED ROOT FILES at ${commit})"
  echo

  local root_files=()
  mapfile -t root_files < <(list_root_files_at_commit "$commit")

  for f in "${root_files[@]}"; do
    # Skip directories (root listing includes trees and blobs)
    local t
    t="$(git cat-file -t "${commit}:${f}" 2>/dev/null || true)"
    [[ "$t" == "blob" ]] || continue

    # Skip pinned duplicates (already included above)
    for pinned in "${ROOT_PINNED_FILES[@]}"; do
      [[ "$f" == "$pinned" ]] && continue 2
    done

    if is_denied_path "$f"; then
      echo "## FILE: ${f} @ ${commit}"
      echo "> Skipped: denied by pattern."
      echo
      continue
    fi

    local size
    size="$(git cat-file -s "${commit}:${f}" 2>/dev/null || echo 0)"
    safe_embed_text "${f} @ ${commit}" "$size" git show "${commit}:${f}"
    echo
  done
}

embed_dir_baseline() {
  local commit="$1"
  echo "## BASELINE CONTENT (${REL_TARGET_DIR}/ at ${commit})"
  echo

  local files=()
  mapfile -t files < <(list_dir_files_at_commit "$commit")

  if [[ "${#files[@]}" -eq 0 ]]; then
    echo "> No files found under ${REL_TARGET_DIR}/ at ${commit}"
    echo
    return 0
  fi

  local f size
  for f in "${files[@]}"; do
    if is_denied_path "$f"; then
      echo "## FILE: ${f} @ ${commit}"
      echo "> Skipped: denied by pattern."
      echo
      continue
    fi
    size="$(git cat-file -s "${commit}:${f}" 2>/dev/null || echo 0)"
    safe_embed_text "${f} @ ${commit}" "$size" git show "${commit}:${f}"
    echo
  done
}

write_baseline() {
  write_header
  if [[ "$EMIT_TREE" == "true" ]]; then
    emit_tree "$BASE_COMMIT"
  fi

  embed_root_files_baseline "$BASE_COMMIT"
  embed_dir_baseline "$BASE_COMMIT"
}

write_changes() {
  write_header

  # Build pathspec: target dir + pinned root files + (optionally) all root files
  local pathspec=( "$REL_TARGET_DIR" )
  pathspec+=( "${ROOT_PINNED_FILES[@]}" )

  if [[ "$INCLUDE_ROOT_ALL" == "true" ]]; then
    # Current tracked root files (non-recursive)
    mapfile -t _root_now < <(git ls-files --max-depth 1 || true)
    for f in "${_root_now[@]}"; do
      pathspec+=( "$f" )
    done
  fi

  local status patch
  status="$(git diff --name-status "${BASE_COMMIT}..HEAD" -- "${pathspec[@]}" || true)"
  patch="$(git diff "${BASE_COMMIT}..HEAD" -- "${pathspec[@]}" || true)"

  echo "## CHANGE SUMMARY (since ${BASE_COMMIT})"
  echo
  if [[ -z "$status" ]]; then
    echo "> No changes detected in scope since ${BASE_COMMIT}"
    echo
  else
    echo '```'
    echo "$status"
    echo '```'
    echo
  fi

  echo "## PATCH (since ${BASE_COMMIT})"
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

  echo "## CURRENT CONTENT OF CHANGED FILES"
  echo

  local changed_files=()
  if [[ -n "$status" ]]; then
    while IFS=$'\t' read -r st p1 p2; do
      [[ -n "${st:-}" ]] || continue

      if [[ "$st" =~ ^R ]]; then
        [[ -n "${p2:-}" ]] && changed_files+=("$p2")
        continue
      fi

      if [[ "$st" == "D" ]]; then
        echo "## FILE: ${p1} @ WORKTREE"
        echo "> Deleted in working tree."
        echo
        continue
      fi

      [[ -n "${p1:-}" ]] && changed_files+=("$p1")
    done <<<"$status"
  fi

  if [[ "${#changed_files[@]}" -eq 0 ]]; then
    echo "> No non-deleted changed files to embed."
    echo
    return 0
  fi

  local f bytes
  for f in "${changed_files[@]}"; do
    if is_denied_path "$f"; then
      echo "## FILE: ${f} @ WORKTREE"
      echo "> Skipped: denied by pattern."
      echo
      continue
    fi

    if [[ ! -f "$f" ]]; then
      echo "## FILE: ${f} @ WORKTREE"
      echo "> Skipped: file not present in working tree."
      echo
      continue
    fi

    bytes="$(wc -c <"$f" | tr -d ' ')"
    safe_embed_text "${f} @ WORKTREE" "$bytes" cat "$f"
    echo
  done
}

write_bashrc() {
  local bashrc="${HOME}/.bashrc"
  echo "## ~/.bashrc"
  echo
  if [[ ! -f "$bashrc" ]]; then
    echo "> Skipped: ${bashrc} not found."
    echo
    return 0
  fi
  local bytes
  bytes="$(wc -c <"$bashrc" | tr -d ' ')"
  safe_embed_text "~/.bashrc @ WORKTREE" "$bytes" cat "$bashrc"
  echo
}

tmp_out="$(mktemp)"
{
  if [[ "$MODE" == "baseline" ]]; then
    write_baseline
  else
    write_changes
  fi

  if [[ "$INCLUDE_BASHRC" == "true" ]]; then
    write_bashrc
  fi
} >"$tmp_out"

mv "$tmp_out" "$OUT_FILE"
echo "Wrote: ${REPO_ROOT}/${OUT_FILE}"
