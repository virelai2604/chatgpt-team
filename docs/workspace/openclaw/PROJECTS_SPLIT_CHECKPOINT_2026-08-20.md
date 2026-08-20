# OpenClaw Project Split Checkpoint — 2026-08-20 Refresh

## Purpose

Refresh the OpenClaw project checkpoint after the 2026-08-20 project registry review.

## Current Status

- [Done] `OpenClaw_Project` exists under `D:\ChatgptDATAB\DB Chatgpt\Projects`.
- [Done] OpenClaw remains separate from `OpenAI_Workspace_Project`.
- [Done] OpenClaw is the local archive/project mirror for OpenClaw / AgentOS / BIFL material.
- [Done] `chatgpt-team` must not be duplicated into `OpenClaw_Project`.
- [Done] Raw OpenClaw archives remain archive artifacts, not indexed source.
- [Done] Compact Markdown summaries and selected source workflows are the preferred review path.
- [Done] No raw JSON/JSONL semantic indexing is authorized.
- [Done] No dedicated OpenClaw semantic index is authorized from the current source scope.
- [Done] No SQLite/Chroma/DuckDB/model/credential files are approved for promotion.

## Current Local Folders

| Folder | Role |
|---|---|
| `00_Project_Admin` | Administrative manifests, extraction logs, promotion manifests |
| `01_Source_Pointers` | External/source pointer records |
| `02_Active_Source` | Selected active source copied from external OpenClaw evidence |
| `03_BIFL_Scripts` | Selected BIFL scripts |
| `04_BIFL_Reports` | Selected BIFL reports |
| `07_Continuity` | Continuity records, compact summaries, reviews |
| `08_Artifacts` | Artifact evidence |
| `09_Archive_Artifacts` | Archive artifacts, ZIP/extracted evidence kept outside active source |

## Completed Historical Work

- [Done] Selected active source copied into `02_Active_Source`.
- [Done] Selected scripts copied into `03_BIFL_Scripts`.
- [Done] Selected reports copied into `04_BIFL_Reports`.
- [Done] Promoted hash manifests were created.
- [Done] ZIP exports were registered by SHA256.
- [Done] ZIP exports were treated as archive artifacts, not indexed source.
- [Done] Sanitized ZIP extraction was completed.
- [Done] Extracted ZIP SHA256 manifests were created.
- [Done] Selected Markdown was copied into continuity staging.
- [Done] Compact Markdown summaries were generated before indexing.
- [Done] Duplicate candidate review found no duplicate candidates in staged Markdown summary workflow.
- [Done] OpenClaw JSON/JSONL archive policy was created: archive-only by default.
- [Done] 39-versus-38 topic-count difference was reconciled as grouping/normalization drift, not missing knowledge.
- [Done] One BIFL data-layer architecture candidate was approved as a local final candidate, not promoted.
- [Done] OpenClaw re-index plan was superseded because current approved material did not justify a dedicated index.
- [Done] OpenClaw primary-source discovery closed with zero approved OpenClaw-specific Project Sources and zero semantic-index approvals.

## Not Done

- [Not done] Promote OpenClaw material into ChatGPT Project Sources.
- [Not done] Build a dedicated OpenClaw index.
- [Not done] Re-index OpenAI Workspace with OpenClaw material.
- [Not done] Promote raw JSON/JSONL exports.
- [Not done] Delete raw archive evidence.
- [Not done] Commit refreshed OpenClaw README/checkpoint to GitHub.
- [Not done] Produce a clean publication copy of the duplicated append-only checkpoint if needed later.

## Superseded

- [Superseded] Blind archive copy as an active-source strategy.
- [Superseded] Raw extracted chat export indexing.
- [Superseded] Raw JSON/JSONL Project Source promotion.
- [Superseded] Building an OpenClaw index from the current 13-file selected-source scope.
- [Superseded] Treating OpenClaw as owner of `chatgpt-team`.

## Hold / Safety

- [Hold] No source deletion.
- [Hold] No archive deletion.
- [Hold] No semantic re-index.
- [Hold] No SQLite mutation.
- [Hold] No Chroma mutation.
- [Hold] No Project Source promotion.
- [Hold] No credential movement.
- [Hold] No raw archive upload to GitHub.

## GitHub Storage Decision

It is acceptable to store lightweight OpenClaw governance documents in GitHub, such as:

- `README.md`;
- selected manifest summaries;
- checkpoint summaries;
- source-selection rules.

It is not acceptable to store heavy/raw OpenClaw evidence in GitHub.

Recommended GitHub location if committed later:

```text
docs/workspace/openclaw/README.md
docs/workspace/openclaw/PROJECTS_SPLIT_CHECKPOINT_2026-08-20.md
```

## Next Actions

1. Replace `OpenClaw_Project\README.md` after review.
2. Replace `OpenClaw_Project\PROJECTS_SPLIT_CHECKPOINT_2026-07-14.md` or add this as a new dated checkpoint.
3. Keep raw archives local.
4. Only promote high-signal, reviewed compact summaries.
5. Do not index OpenClaw until a separate isolated-index design is approved.
