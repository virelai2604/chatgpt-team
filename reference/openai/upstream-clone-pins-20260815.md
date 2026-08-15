# OpenAI Upstream Reference Pins — 2026-08-15 (batch 2)

Dated HEAD-commit pins for additional OpenAI upstream repositories.
**Pointer-only** — the repositories are **not vendored** into this repo; only their
provenance is recorded. Machine-readable form:
`reference/manifests/openai_upstream_pins_20260815.json`.
Extends the 2026-08-14 batch (`upstream-clone-pins-20260814.md`: agents-python, cookbook, evals).

Verification: each HEAD was resolved on 2026-08-15 via `git ls-remote --symref <url> HEAD`
(existence + HEAD SHA confirmed; **no clone**, so commit dates are not captured here).

| Repo | Pinned commit (HEAD) | Branch |
|---|---|---|
| `openai/sites` | `9d3c7dd5e24ddd9058f5242a835c08b72b3f1069` | main |
| `openai/openai-node` | `6827a403bfb4d93d86a59769faa4b24a95837823` | main |
| `openai/openai-cli` | `3023717289fdafce3e13f06fe613fac592391d2a` | main |
| `openai/evals` | `8eac7a7de5215c907fbddc30efdaf316913eccdd` | main *(matches 2026-08-14 pin)* |
| `openai/tiktoken` | `08a5f3b2c987ada4fc5aa1f16c643c203fa8acaa` | main |
| `openai/codex` | `4861236f06d0df397436531b4aa3d7fa6975959c` | main |
| `openai/openai-python` | `10ee3f0da2ac6f93345c1204bd7bb1a2faa79ff2` | main |
| `openai/codex-action` | `c385816875cc2fc8e033ed9d1cba96f8c331210e` | main |
| `openai/plugins` | `11c74d6ba24d3a6d48f54a194cd00ef3beea18f9` | main |
| `openai/openai-developers-for-claude` | `3c5c0debdec2695f657c5f1b99a32df6d23dd0ed` | main |
| `openai/openai-developers-for-cursor` | `9120f1f6bb47964651ab822e24b4f358e3638ae3` | main |
| `openai/chatgpt-retrieval-plugin` | `b28ddce58474441da332d4e15c6dd60ddaa953ab` | main |

## Relationship to the canonical register

Where a repo already has a `source-register.jsonl` row (`gh_openai_node`, `gh_openai_python`,
`gh_openai_plugins`, `evals`), this file refreshes its provenance date without modifying the
canonical row. The rest are newly recorded pointers. `chatgpt-retrieval-plugin` is historical
retrieval architecture — kept as a reference pointer, not a current default.

## How to use

Clone any repo locally at its pinned commit (do not commit it back):

```bash
git clone --filter=blob:none https://github.com/openai/codex.git
git -C codex checkout 4861236f06d0df397436531b4aa3d7fa6975959c
```

Distill needed material into a summary under `reference/openai/`; never vendor the full
upstream tree (see `docs/policies/p4_index_pointer.md` and
`docs/policies/openai_workspace_index_exclusion_policy.md`).
