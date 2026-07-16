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
source_url           canonical URL (may be a docs page that is NOT itself fetchable here)
source_type          official_docs | official_github | official_cookbook
retrieved_at         ISO date the snapshot/verification was made
pull_status          fetched | web_verified | summary_only | pointer_only
authority            primary | secondary
freshness_class      volatile | moderate | stable   (how fast it rots)
local_snapshot       path to the in-repo file (or note)
supersedes           [old source_ids this row replaces]
verification_status  verified | web_verified | partial | GAP | deprecated
docs_page_fetched    (optional) false when source_url is a 403 docs page that was NOT fetched
fetched_from         (optional) the actual retrieved artifact backing a `fetched` row
note                 optional
```

**Status precedence on conflict:** `fetched` > `web_verified` > `summary_only` > `pointer_only`.

**What `fetched` means here:** the row is derived from a genuinely retrieved artifact.
When `source_url` is a **403-blocked docs page** (`platform`/`developers`/`help`/`openai.com`),
that page itself was **not** fetched — the real artifact is a GitHub source (the OpenAPI
spec, a repo README, a cookbook notebook), named in **`fetched_from`**, and the row carries
**`docs_page_fetched: false`**. So a `fetched` status never implies the docs page is a
durable local snapshot.

**Gap-triage rule:** judge durability from **`fetched_from` / `local_snapshot`**, NOT from
`source_url`. A row with `docs_page_fetched: false` still needs a browser pass to promote the
*docs page* to a true snapshot, even though its underlying artifact is fetched.

**Freshness rule:** `volatile` rows (pricing, models, availability) must be **re-verified before use** — never treated as durable truth.

## Coverage snapshot (2026-07-16)

- **27 canonical sources**; 17 docs, 8 GitHub, 2 cookbook.
- **Fetched or web-verified:** 23.
- **Resolved:** `workspace_agent_auth` — `summary_only` → **`fetched`** (2026-07-16);
  snapshot at `workspace-agents/workspace-agent-authentication.md`, `docs_page_fetched:true`
  (live official page supplied via browser). Token rotation/lifetime still not documented on the page.
- **Open GAPs (3)** — pull priority order:
  1. `gh_openai_agents_js` — not yet pulled (JS SDK 0.13.2).
  2. `gh_openai_cookbook` — selected notebooks only (Responses / File Search / Agents / Evals).
  3. `gh_openai_node` — README/changelog metadata only.

  _Resolved:_ `gh_openai_apps_sdk_examples` → `fetched` (2026-07-16),
  snapshot at `apps-sdk/openai-apps-sdk-examples.md`.

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
