# Milestone — GitHub OpenAI Reference Pull Checkpoint

- **Date:** 2026-07-07
- **Repo:** virelai2604/chatgpt-team
- **Local workspace:** `C:\Users\User\Desktop\Agent\Openclaw\chatgpt-team`
- **Durable mirror target:** `D:\ChatgptDATAB\DB Chatgpt\Projects\OpenAI_Workspace_Project\01_OpenAI_Docs_Summaries\`

## Done (version-controlled in the repo)

| PR | Result |
|---|---|
| #15 | Reference catalog — `reference/openai/SOURCES.md` + `sources.json` (top-10 docs + 7 repos + rules; `openai/skills` flagged deprecated → `openai/plugins`) |
| #16 | Top-4 P0 snapshots + `openai-reference-manifest.jsonl` |

### Snapshot provenance (honest)

| File | pull_status |
|---|---|
| `workspace-agents/workspace-agent-trigger-runs.md` | fetched |
| `cookbook/workspace-agent-api-trigger.md` | fetched |
| `github-openai/openai-plugins-repo-summary.md` | fetched |
| `apps-sdk/build-mcp-server.md` | **summary_only** (developers.openai.com 403 to bots) |
| `openai-reference-manifest.jsonl` | accession ledger |

Captured contract: `POST https://api.chatgpt.com/v1/workspace_agents/{id}/trigger`,
`Authorization: Bearer <agent token>` (NOT the OpenAI API key), `Idempotency-Key`,
body `{input, conversation_key}`, → `202 Accepted` (async, no body/run id).

## Open items (not proven — require local action)

| Item | Owner | How |
|---|---|---|
| Sync repo `reference/openai/` → Windows mirror | you (local) | `git pull` then copy into `01_OpenAI_Docs_Summaries\` |
| Ingest reference files into SQLite/Chroma | you (local) | run your indexer over `reference/openai/` |
| Full `apps-sdk/build-mcp-server` snapshot | you (browser) | open the URL in a browser, replace the summary body, set `pull_status: fetched` |

## Local commands

```powershell
cd C:\Users\User\Desktop\Agent\Openclaw\chatgpt-team
git pull

# mirror the reference snapshots into the durable project store
robocopy ".\reference\openai" "D:\ChatgptDATAB\DB Chatgpt\Projects\OpenAI_Workspace_Project\01_OpenAI_Docs_Summaries" /E
```

Then index (WSL): point your existing indexer at the mirrored folder — SHA256
chunk ids dedupe automatically, so re-running is safe.

## Truth line

- GitHub PR #15 = catalog created ✅
- GitHub PR #16 = top-4 references pulled ✅
- Windows mirror sync = pending (local)
- SQLite/Chroma ingest = pending (local)
