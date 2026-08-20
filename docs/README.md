# docs/

Governance, status checkpoints, and workspace registries for the
`chatgpt-team` relay.

For the **project overview** (what the relay is, API surfaces, guardrails,
quickstart) see the repository root [`README.md`](../README.md). The relay runs
on **Render** (`render.yaml`, service `chatgpt-team-relay`, health check
`/v1/health`) via `uvicorn app.main:app`; CI is `.github/workflows/ci.yml`
(ruff + pytest + Gitleaks). This folder holds documentation only — no code.

## policies/

Source-hygiene and write-target rules.

- [`WRITE_TARGET_POLICY.md`](policies/WRITE_TARGET_POLICY.md)
- [`database-role-map.md`](policies/database-role-map.md)
- [`openai_workspace_index_exclusion_policy.md`](policies/openai_workspace_index_exclusion_policy.md)
- [`p4_index_pointer.md`](policies/p4_index_pointer.md) — the local retrieval
  index (SQLite/Chroma) stays local; commit pointers and checkpoints only.

## status/

Dated verification checkpoints. Each is a **historical** snapshot with its own
date and explicit "not proven" caveats — never a claim of current runtime health.

- [`archive_intake_audit_20260814.md`](status/archive_intake_audit_20260814.md)
- [`source_manifest_preflight_v5_final_consistency_closure_20260813_221526.md`](status/source_manifest_preflight_v5_final_consistency_closure_20260813_221526.md)
- [`openai_workspace_current_retrieval_eval_state_20260721.md`](status/openai_workspace_current_retrieval_eval_state_20260721.md)
- [`openai_workspace_post_cleanup_project_source_verification_20260721.md`](status/openai_workspace_post_cleanup_project_source_verification_20260721.md)
- [`p4_v2_5_6_reconciliation_20260815.md`](status/p4_v2_5_6_reconciliation_20260815.md) — P4 spec reconciled to active v2.5.6.

## workspace/

Project-split registries for the local OpenAI Workspace / OpenClaw projects
(pointer-only; local paths are recorded, not their contents).

- [`PROJECTS_REGISTRY_2026-08-20.md`](workspace/PROJECTS_REGISTRY_2026-08-20.md)
- [`PROJECTS_SPLIT_CHECKPOINT_2026-08-20.md`](workspace/PROJECTS_SPLIT_CHECKPOINT_2026-08-20.md)
- [`openclaw/README.md`](workspace/openclaw/README.md)
- [`openclaw/PROJECTS_SPLIT_CHECKPOINT_2026-08-20.md`](workspace/openclaw/PROJECTS_SPLIT_CHECKPOINT_2026-08-20.md)

## Related

- Curated OpenAI reference material lives under
  [`reference/openai/`](../reference/openai/) (docs summaries, source register,
  upstream pins) and is indexed from [`OPENAI_REFERENCES.md`](../OPENAI_REFERENCES.md).
