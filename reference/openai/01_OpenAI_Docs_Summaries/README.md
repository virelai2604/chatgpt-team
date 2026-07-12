# 01_OpenAI_Docs_Summaries

Official OpenAI documentation **evidence track**. Source-of-truth summaries of
OpenAI's own docs, kept honest about provenance so nothing here is mistaken for
a verbatim snapshot when it isn't.

## Sources (source-of-truth inputs)

- **@OpenAI Developers** — official OpenAI developer / API evidence
  (`developers.openai.com`, `platform.openai.com/docs`, `openai.com`).
- **@openai-docs** — official OpenAI documentation summaries
  (Help Center `help.openai.com`, Platform, API reference, Cookbook
  `github.com/openai/openai-cookbook`, and the official SDK/spec repos under
  `github.com/openai`).

## Verification policy (why this track exists)

OpenAI facts drift constantly. **Re-verify against the live source** whenever a
fact is:

- current / time-sensitive,
- model-specific (names, families, context windows),
- API-specific (endpoints, params, request/response shapes),
- pricing-related,
- availability / rollout-related,
- connector-related, or
- tool-related.

**Do not rely on old chat memory** for any of the above. Each summary carries a
`source_urls` list — open it and reconcile before acting on a
current/model/API/pricing/availability/connector/tool detail.

> Example of drift caught during authoring (2026-07-12, via live web search):
> the API flagship is **GPT-5.5** ($5.00 / $30.00 per 1M), the **GPT-5.6**
> family (Sol / Terra / Luna) shipped, and **GPT-5.4** remains available — none
> of which matches older assumptions. Treat every model/pricing line as
> perishable.

## Provenance legend (`pull_status` in each file's frontmatter)

| status | meaning |
|---|---|
| `fetched` | Body derived from content actually retrieved this session (a fetchable GitHub source: SDK repo, `openai-openapi` spec, cookbook, examples). |
| `web_verified` | Doc site is not directly fetchable here, but key facts were confirmed via live web search on the authoring date. Still verify the exact wording at `source_urls`. |
| `summary_only` | Doc site blocked automated fetch (`platform`/`developers`/`help` return 403 from this environment). Body is a best-effort summary — **open `source_urls` in a browser and reconcile.** |

## Fetchability note (authoring environment, 2026-07-12)

- ✅ `raw.githubusercontent.com` / `github.com/openai/*` — fetchable.
- ❌ `platform.openai.com`, `developers.openai.com`, `help.openai.com`,
  `openai.com` — return HTTP 403 to automated fetch. Facts from these were
  cross-checked via web search (`web_verified`) or flagged `summary_only`.

## Contents

| # | File | pull_status |
|---|---|---|
| 01 | `01-chatgpt-projects.md` | see file |
| 02 | `02-chatgpt-capabilities-overview.md` | see file |
| 03 | `03-prompt-guidance.md` | see file |
| 04 | `04-agent-skills.md` | see file |
| 05 | `05-openai-platform.md` | see file |
| 06 | `06-responses-api.md` | see file |
| 07 | `07-file-search.md` | see file |
| 08 | `08-vector-stores.md` | see file |
| 09 | `09-tools-and-connectors.md` | see file |
| 10 | `10-evals.md` | see file |
| 11 | `11-embeddings.md` | see file |
| 12 | `12-apps-sdk.md` | see file |
| 13 | `13-agents-sdk.md` | see file |
| 14 | `14-realtime.md` | see file |
| 15 | `15-api-keys-projects-organizations.md` | see file |

See `manifest.jsonl` for machine-readable provenance (one row per summary).
