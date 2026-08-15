# tests/test_cursor_rules.py
"""Cursor rule files must stay parseable and must point at real code.

Why this exists
---------------
`.cursor/rules/*.mdc` files are silent when wrong. Cursor does not report a bad
frontmatter block or a glob that matches nothing -- the rule simply never attaches,
and the assistant goes on answering without the constraint it was supposed to have.
That failure looks exactly like everything working.

The same drift already happened to `static/.well-known/ai-plugin.json`, which pointed
at `/openapi.yaml` (404) and `/v1/tools` (404) for months because nothing checked.

These tests pin the three things that make a rule actually fire.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / ".cursor" / "rules"

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _rules() -> list[Path]:
    return sorted(RULES.glob("*.mdc"))


def test_rules_directory_is_not_empty() -> None:
    assert _rules(), f"{RULES} has no .mdc files — did they get moved or deleted?"


@pytest.mark.parametrize("path", _rules(), ids=lambda p: p.name)
def test_frontmatter_parses_and_declares_activation(path: Path) -> None:
    """A rule with no valid frontmatter never attaches, and Cursor says nothing."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER.match(text)
    assert m, f"{path.name}: missing the leading `---` YAML frontmatter block"

    fm = yaml.safe_load(m.group(1)) or {}
    assert isinstance(fm, dict), f"{path.name}: frontmatter is not a mapping"

    assert "alwaysApply" in fm, f"{path.name}: must declare alwaysApply explicitly"
    assert isinstance(fm["alwaysApply"], bool), f"{path.name}: alwaysApply must be a bool"

    # Every activation mode except Always needs something to match on: globs for
    # auto-attach, or a description for the agent-requested mode. With neither, the
    # rule can only ever be invoked by hand.
    if not fm["alwaysApply"]:
        assert fm.get("globs") or fm.get("description"), (
            f"{path.name}: alwaysApply is false with no globs and no description, "
            "so this rule can never attach on its own"
        )

    assert text[m.end():].strip(), f"{path.name}: frontmatter but no rule body"


@pytest.mark.parametrize("path", _rules(), ids=lambda p: p.name)
def test_globs_match_files_that_exist(path: Path) -> None:
    """A glob matching nothing is a rule that never fires."""
    fm = yaml.safe_load(FRONTMATTER.match(path.read_text(encoding="utf-8")).group(1)) or {}
    globs = fm.get("globs")
    if not globs:
        pytest.skip("no globs — agent-requested or always-applied rule")

    patterns = [g.strip() for g in (globs if isinstance(globs, list) else globs.split(","))]
    for pattern in patterns:
        assert list(REPO.glob(pattern)), (
            f"{path.name}: glob {pattern!r} matches no files in the repo, "
            "so this rule will never attach"
        )
