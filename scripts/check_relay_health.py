"""
scripts/check_relay_health.py

Convenience script:
1. Print component mapping (sanity of project layout).
2. Run pytest to verify routes, tools, and forward API behavior.
"""

from pathlib import Path
import subprocess
import sys

# REPO_ROOT is one level above scripts/
REPO_ROOT = Path(__file__).resolve().parents[1]


def run_component_map() -> int:
    """Run print_component_map.py from the repo root."""
    script = REPO_ROOT / "print_component_map.py"
    if not script.exists():
        print("print_component_map.py not found in repo root", file=sys.stderr)
        return 1

    print("=== COMPONENT MAP ===")
    # Run with cwd=REPO_ROOT so paths resolve like your manual runs.
    return subprocess.call([sys.executable, str(script)], cwd=str(REPO_ROOT))


def run_pytest() -> int:
    """Run pytest from the repo root."""
    print("\n=== PYTEST ===")
    return subprocess.call([sys.executable, "-m", "pytest"], cwd=str(REPO_ROOT))


def main() -> None:
    rc_map = run_component_map()
    if rc_map != 0:
        print("\nComponent map check failed (missing files or script).", file=sys.stderr)

    rc_pytest = run_pytest()
    if rc_pytest != 0:
        print("\nPytest reported failures. Inspect tests and logs.", file=sys.stderr)

    if rc_map == 0 and rc_pytest == 0:
        print("\nAll checks passed: layout + tests are green.")


if __name__ == "__main__":
    main()
