# OpenAI Upstream Reference Pins — 2026-08-14

Dated commit pins for the OpenAI upstream repositories this project references.
**Pointer-only** — the repositories are **not vendored** into this repo (they are large
and would violate the source-hygiene policy); only their provenance is recorded here.
Machine-readable form: `reference/manifests/openai_upstream_pins_20260814.json`.

Verification: each was `git clone --depth 1 --filter=blob:none`'d on 2026-08-14 and its
HEAD commit recorded.

| Repo | Pinned commit | Commit date | Clone URL |
|---|---|---|---|
| `openai/openai-agents-python` | `0b93ce8faa27d4631df399fe48856b52a8fd9897` | 2026-08-14 | `https://github.com/openai/openai-agents-python.git` |
| `openai/openai-cookbook` | `4a85c3018d20ceef48bf7549450c567896501bf9` | 2026-08-05 | `https://github.com/openai/openai-cookbook.git` |
| `openai/evals` | `8eac7a7de5215c907fbddc30efdaf316913eccdd` | 2026-04-14 | `https://github.com/openai/evals.git` |

## Relationship to the canonical register

These refresh the July-12 provenance of the existing `source-register.jsonl` rows
(`gh_openai_agents_python`, `gh_openai_cookbook`, and the `evals` row that folds in
`gh_openai_evals`). The canonical register rows are **not modified** here; this file is an
additive, dated re-verification pointer.

## How to use

To read a repo locally, clone it yourself at the pinned commit (do not commit it back):

```bash
git clone --filter=blob:none https://github.com/openai/openai-agents-python.git
git -C openai-agents-python checkout 0b93ce8faa27d4631df399fe48856b52a8fd9897
```

Distill any needed material into a summary under `reference/openai/`; never vendor the
full upstream tree (see `docs/policies/p4_index_pointer.md` and
`docs/policies/openai_workspace_index_exclusion_policy.md`).
