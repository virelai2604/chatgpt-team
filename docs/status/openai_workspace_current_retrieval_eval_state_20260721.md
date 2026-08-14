# Retrieval Eval State — 2026-07-21 (HISTORICAL)

> **Historical checkpoint.** These metrics were recorded on **2026-07-21** for the local
> OpenAI Workspace RAG pipeline. They are **not** a claim of current retrieval health.
> Re-run a read-only smoke check before treating any value here as current.

## Recorded baseline

| Metric | Value | Source / date |
|---|---|---|
| Retrieval smoke result | 10 / 10 pass | Local eval run, 2026-07-17 → 2026-07-21 checkpoint |
| Recall@10 | `1.0000` | Same run |
| MRR | `0.9500` | Same run |
| Rebuild / re-index during checkpoint | Not done | Documentation/recovery only |

## Provenance

- Read-only recurring-eval schedule checklist (gatekeeper before any eval run):
  `openai_workspace_recurring_eval_read_only_schedule_checklist_20260720.md`
  SHA-256 `7D1818FC3DB4912B28A4022644B3878BB1CF0050BA754A3CDB5C0C45891C60D5`.
- The checklist exists; eval execution remained **gated** — no eval was run merely to
  produce this record.

## Explicitly not claimed

- Current Chroma health after any later source change — **not proven**.
- That a fresh smoke check still returns 10/10 today — **not proven**.
- Any authorization to rebuild, re-index, or mutate SQLite/Chroma.
