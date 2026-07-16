# OpenAI Reference — Canonical Source Register

**`source-register.jsonl` is the single source of truth** for what OpenAI
reference material this repo holds, its provenance, and its freshness. It
reconciles the previously overlapping manifests into one register.

_Reconciled 2026-07-16 from the four prior catalogs._

## Why this exists

Four overlapping catalogs had drifted apart with different status vocabularies:

| File | New role after reconciliation |
|---|---|
| `01_OpenAI_Docs_Summaries/manifest.jsonl` | **Current authoritative snapshots** (July-12 set) — its records win on conflict |
| `openai-reference-manifest.jsonl` | **Historical accession ledger** (July-07 pull) — superseded rows folded into the register |
| `sources.json` | **Priority/purpose catalog** — kept for the "what to pull & why" ranking |
| `SOURCES.md` | **Human-readable index** — narrative companion |

The old files are **retained, not deleted** (reconciliation-review rule). Treat
`source-register.jsonl` as canonical; the others as compatibility/historical.

## Record schema (each line of `source-register.jsonl`)

```
source_id            stable key
source_url           canonical URL
source_type          official_docs | official_github | official_cookbook
retrieved_at         ISO date the snapshot/verification was made
pull_status          fetched | web_verified | summary_only | pointer_only
authority            primary | secondary
freshness_class      volatile | moderate | stable   (how fast it rots)
local_snapshot       path to the in-repo file (or note)
supersedes           [old source_ids this row replaces]
verification_status  verified | web_verified | partial | GAP | deprecated
note                 optional
```

**Status precedence on conflict:** `fetched` > `web_verified` > `summary_only` > `pointer_only`.
**Freshness rule:** `volatile` rows (pricing, models, availability) must be **re-verified before use** — never treated as durable truth.

## Coverage snapshot (2026-07-16)

- **27 canonical sources**; 17 docs, 8 GitHub, 2 cookbook.
- **Fetched or web-verified:** 22.
- **Open GAPs (5)** — pull priority order:
  1. `workspace_agent_auth` — official page still `summary_only` → `_pending_summaries.md`. **Pull first** (agent token vs API key, trigger scope, secret storage).
  2. `gh_openai_apps_sdk_examples` — not yet pulled (example MCP servers + UI).
  3. `gh_openai_agents_js` — not yet pulled (JS SDK 0.13.2).
  4. `gh_openai_cookbook` — selected notebooks only (Responses / File Search / Agents / Evals).
  5. `gh_openai_node` — README/changelog metadata only.

## Fetchability note (this environment)

- ✅ `github.com/openai/*`, `raw.githubusercontent.com` — fetchable → `fetched`.
- ❌ `platform.openai.com`, `developers.openai.com`, `help.openai.com` — **HTTP 403** to
  automated fetch. Facts from those are `web_verified` (live search) or `summary_only`
  and must be reconciled against the page **in a browser** to become `fetched`.

## Superseded map (what the register replaced)

| Superseded (old id) | Replaced by (canonical) |
|---|---|
| `oa_file_search` | `file_search` (07) |
| `oa_skills_tools` | `agent_skills` (04) |
| `oa_agents_sdk` | `agents_sdk` (13) |
| `oa_apps_sdk_build_mcp_server`, `oa_apps_sdk_mcp_apps` | `apps_sdk` (12) |
| `gh_openai_evals` | `evals` (10) |

## Do NOT

- Copy pricing/model tables as durable truth (they're `volatile`).
- Vendor full SDK repos into this repo (metadata + selected files only).
- Treat `openai/skills` as active (deprecated → `openai/plugins`).
- Duplicate a source already represented by a newer canonical row.
