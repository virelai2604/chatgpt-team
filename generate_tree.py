#!/usr/bin/env python3
"""
Clean Project Tree Generator
Generates a minimal, readable project structure with 📁 folders and 📄 files.
Outputs to `project-tree.md` at repo root.
"""

import os

# Excluded directories and file patterns (noise)
EXCLUDE_DIRS = {
    ".git", ".github", ".venv", "__pycache__", ".pytest_cache",
    "site-packages", "dist", "build", ".mypy_cache", ".idea", ".vscode"
}
EXCLUDE_FILES = {
    ".DS_Store", "Thumbs.db", "pyproject.toml", "Pipfile.lock"
}

OUTPUT_FILE = "project-tree.md"

def is_excluded(path):
    parts = path.split(os.sep)
    return any(p in EXCLUDE_DIRS for p in parts)

def generate_tree(root_dir="."):
    lines = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter ignored dirs in place
        dirnames[:] = [d for d in dirnames if not is_excluded(os.path.join(dirpath, d))]

        if is_excluded(dirpath):
            continue

        depth = dirpath.count(os.sep)
        indent = "  " * (depth)
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

def main():
    print("Generating clean project tree...")
    tree = generate_tree(".")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(tree)
    print(f"✅ Clean tree saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
