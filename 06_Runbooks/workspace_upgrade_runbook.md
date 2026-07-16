# OpenAI Workspace Upgrade Runbook

_Verified and revised against current OpenAI documentation, 2026-07-16._
_Scope: OpenAI_Workspace_Project retrieval, agent, and governance architecture._
_Status: documentation-only plan. No index rebuild, database mutation, relay change, or production deployment is authorized by this runbook._

---

## 0. Current accepted baseline

Baseline label:

`openai_workspace_rag_final_clean_baseline_2026-07-16`

Accepted local state:

- SQLite `integrity_check`: `ok`
- Files: `212`
- Documents: `212`
- Chunks: `550`
- FTS rows: `550`
- Chunk embeddings: `550`
- Chroma document count: `212`
- Chroma chunk count: `550`
- Active chunk collection: `openai_workspace_chunks_3large_1024`
- Embedding model: `text-embedding-3-large`
- Embedding dimensions: `1024`

**Control rule:** do not rebuild or re-index this baseline unless a source update, exclusion-policy change, or indexing-script change is explicitly authorized.

---

## 1. Architecture decision

Use two retrieval tracks with different roles.

### Track A — authoritative local retrieval

The local stack remains the durable source-backed retrieval system:

- raw files remain the source of truth;
- SHA-256 manifests prove file and content identity;
- SQLite stores authoritative file, document, chunk, FTS, dedupe, and checkpoint records;
- Chroma provides local semantic retrieval;
- Windows is the durable write target;
- WSL is the execution engine only.

Local vectors must remain model- and dimension-consistent within each collection. The accepted OpenAI Workspace collection uses `text-embedding-3-large` at `1024` dimensions.

### Track B — optional hosted retrieval

OpenAI File Search may be used for a curated hosted corpus:

- upload only approved, distilled documents;
- use OpenAI Vector Stores with the Responses API `file_search` tool;
- manage access, lifecycle, deletion, cost, and evaluation separately from the local stack;
- do not upload raw repositories, raw recovery data, credentials, database files, or the complete BIFL corpus by default;
- do not mirror every local SQLite/Chroma chunk into OpenAI Vector Stores.

OpenAI manages parsing, chunking, embedding, and hosted retrieval. Do not impose the local collection's `1024`- or `1536`-dimension configuration on OpenAI-hosted Vector Stores.

---

## 2. Upgrade priority

Execute in this order:

1. preserve and measure the accepted local baseline;
2. inventory Assistants API dependencies;
3. define a curated hosted File Search pilot;
4. compare local and hosted retrieval with the same evaluation questions;
5. add governed Agents SDK workflows where custom control is required;
6. configure thin Workspace Agents for team-facing automations;
7. retire legacy paths only after replacement equivalence is proven.

---

## Phase 1 — Preserve and evaluate local retrieval

### Purpose

Protect the clean `212/550` baseline before introducing hosted retrieval or agent changes.

### Procedure

1. Record current SQLite, FTS, embedding, and Chroma counts.
2. Run the existing hybrid smoke queries.
3. Create or update a recurring retrieval evaluation set.
4. Classify failures separately:
   - keyword retrieval miss;
   - semantic retrieval miss;
   - ranking failure;
   - synthesis failure;
   - citation or provenance failure.
5. Do not change indexing scripts, exclusions, chunking, or embeddings in this phase.

### Exit gate

- SQLite integrity remains `ok`.
- SQLite chunks, FTS rows, embeddings, and Chroma vectors remain `550`.
- Existing smoke-test rank-one results do not regress.
- No rebuild was performed.

---

## Phase 2 — Assistants API inventory and migration plan

The Assistants API is deprecated and scheduled to sunset on **2026-08-26**. New development should use the Responses API, but existing flows must be migrated incrementally rather than deleted first.

### Inventory each Assistants flow

Record:

- endpoint and SDK method;
- assistant/thread/run state usage;
- files and vector stores;
- tools and tool-call handling;
- streaming behavior;
- structured outputs;
- error and retry behavior;
- production caller;
- replacement owner;
- test coverage.

### Migration sequence

For each flow:

1. implement an equivalent Responses API path;
2. verify state handling using `previous_response_id` or Conversations where appropriate;
3. compare tool calls, streaming events, output schemas, latency, token use, errors, and citations;
4. run retrieval and application regression tests;
5. route limited traffic to the replacement;
6. retire the Assistants path only after equivalence is proven.

### Exit gate

Every retired Assistants path has:

- a named Responses replacement;
- passing regression evidence;
- rollback instructions;
- an explicit retirement record.

---

## Phase 3 — Curated hosted File Search pilot

### Candidate store layout

The following is a starting hypothesis, not a mandatory design:

- `ws-openai-sdk`
- `ws-apps-sdk`
- `ws-api-spec`
- `ws-cookbook`
- `ws-evals-history`
- `ws-bifl-curated`

Split stores only when domain, permission, lifecycle, or retrieval-evaluation evidence supports the boundary.

### Pilot corpus rules

Include only:

- current, distilled Markdown or text;
- verified source summaries;
- approved runbooks;
- compact architecture references;
- provenance-bearing documents.

Exclude:

- raw Git clones;
- `.git`, `node_modules`, caches, and build outputs;
- raw notebook outputs;
- generated eval reports;
- SQLite, WAL, SHM, Chroma, and DuckDB files;
- `.env`, keys, cookies, tokens, and credential logs;
- protected recovery paths and raw BIFL recovery evidence.

### Pilot procedure

1. create an approved hosted-file manifest;
2. hash every source file;
3. upload only manifest-approved files;
4. record OpenAI file IDs and vector-store IDs outside source control;
5. wait for processing completion;
6. run at least three representative queries per candidate domain;
7. compare relevance, citations, latency, and cost against:
   - the local hybrid baseline;
   - a less-split hosted-store candidate;
8. promote only if evaluation evidence supports the split.

### Exit gate

- Hosted manifest matches uploaded files.
- No prohibited file was uploaded.
- Retrieval quality is measured, not assumed.
- Store separation has an evidence-backed reason.

---

## Phase 4 — Local ingest pipeline

This phase applies only when a separately authorized source, exclusion, or indexing change requires a local rebuild.

```text
verify source and provenance
  -> distill approved high-signal documents
  -> normalize content
  -> assign stable SHA-256 content/chunk identifiers
  -> update SQLite document and chunk ledgers
  -> update FTS5
  -> generate local embeddings with the collection's fixed model and dimensions
  -> upsert Chroma using the same local chunk identifiers
  -> verify counts and orphan checks
  -> run the retrieval evaluation set
  -> compare against the accepted baseline
```

Do not combine this pipeline with hosted File Search ingestion. Hosted Vector Stores consume approved files and use OpenAI-managed indexing.

### Required exclusions

Retain and extend the existing exclusion policy for:

- raw repositories and `.git`;
- dependency and cache directories;
- raw notebook outputs;
- generated eval/result reports;
- backups, broken stores, and superseded recovery artifacts;
- secrets and runtime credentials.

### Exit gate

- SQLite integrity is `ok`.
- SQLite, FTS, embedding, and Chroma counts agree.
- No orphaned chunk IDs exist.
- Evaluation does not regress.
- A rollback checkpoint exists.

---

## Phase 5 — Agents SDK layer

Use the Agents SDK for workflows requiring custom orchestration or control.

Recommended base:

- `Agent`
- `Runner`
- Sessions/state
- Tracing
- function or MCP tools
- input/output/tool guardrails
- human approval for mutations
- sandbox agents only where isolated file/command work is appropriate

### Retrieval attachment

Attach only the retrieval surface required for the workflow:

- local BIFL search/fetch tools for authoritative local retrieval;
- OpenAI `FileSearchTool` for an approved hosted vector store;
- never attach every store automatically.

### Relay compatibility rule

Do not assume that setting `base_url` to `https://ai.lafiel.me/v1` makes every Agents SDK capability compatible.

Before routing an SDK workflow through the relay, test the exact operations it needs:

- Responses request and response schemas;
- streaming event types and ordering;
- tool-call IDs and tool-output continuation;
- errors and status codes;
- files and uploads;
- vector-store endpoints;
- hosted-tool behavior;
- state and conversation expectations;
- tracing behavior where applicable.

Use OpenAI directly for any SDK feature the relay does not faithfully implement.

---

## Phase 6 — Governance and human approval

Prompt guardrails are not sufficient for destructive operations. Enforce controls at the tool boundary.

For every mutating filesystem or database tool:

1. resolve and normalize the target path;
2. reject protected paths;
3. display the exact proposed operation;
4. require explicit human approval for that operation;
5. bind approval to source, destination, action, and target;
6. revalidate immediately before execution;
7. record approval, execution result, and hashes in an audit ledger.

Protected locations include:

- `<PROTECTED_RECOVERY_ROOT>`
- `<PROTECTED_RECOVERY_SUBTREE>`

Additional rules:

- no write, move, overwrite, or delete without explicit authorization;
- no keeper-file export;
- Phase 10 remains off;
- no credential material in prompts, traces, logs, or repositories.

---

## Phase 7 — Workspace Agents

Use Workspace Agents as thin, team-facing automation surfaces.

Suitable uses:

- scheduled summaries;
- API-triggered repeatable workflows;
- team-accessible research or operational helpers;
- narrow tasks with clear start, stop, and escalation rules.

Keep authoritative state and complex mutation logic outside the GUI agent.

Each Workspace Agent should define:

- responsibility;
- allowed tools and sources;
- trigger;
- stop conditions;
- escalation conditions;
- prohibited operations;
- expected output;
- cost and frequency limits.

Measure real usage before broad rollout.

---

## Phase 8 — Evaluation strategy

### Local retrieval gate

- SQLite integrity is `ok`.
- Chunk count equals FTS count.
- Chunk count equals embedding count.
- Chunk count equals Chroma vector count.
- No missing or orphaned chunk IDs.
- Existing retrieval evals do not regress against the accepted `212/550` baseline.

### Hosted File Search gate

- Uploaded-file manifest matches the approved corpus.
- No prohibited or credential-bearing file was uploaded.
- Representative domain questions retrieve the expected files.
- Citations point to the correct uploaded sources.
- Latency and cost are recorded.
- Split and unsplit candidates are compared before promotion.

### Agent gate

- tool selection is correct;
- unauthorized writes are blocked;
- human approval interrupts occur before mutations;
- traces contain no secrets;
- failure and rollback behavior is tested;
- model, prompt, retrieval, and tool changes are evaluated separately.

### Evaluation platform note

OpenAI's legacy Evals platform is scheduled to become read-only on **2026-10-31** and shut down on **2026-11-30**. Use current OpenAI Datasets/evaluation workflows for new hosted evaluation work. Preserve older Evals examples only as historical migration evidence.

---

## Verification checklist

### Baseline preservation

- [ ] SQLite integrity remains `ok`
- [ ] Files/documents remain `212/212`
- [ ] Chunks/FTS/embeddings remain `550/550/550`
- [ ] Chroma documents/chunks remain `212/550`
- [ ] No rebuild occurred without authorization

### Hosted pilot

- [ ] Approved file manifest exists
- [ ] Every file has SHA-256 provenance
- [ ] No prohibited file was uploaded
- [ ] Query results and citations were reviewed
- [ ] Cost and latency were recorded
- [ ] Store split was justified by evaluation

### Migration

- [ ] Assistants dependencies inventoried
- [ ] Responses replacements implemented
- [ ] Behavioral equivalence tested
- [ ] Rollback available
- [ ] Legacy path retired only after proof

### Governance

- [ ] Protected paths rejected
- [ ] Human approval required per mutation
- [ ] Approval bound to exact operation
- [ ] Audit record written
- [ ] No secrets in repository, logs, or traces

---

## Rollback and recovery

- Keep the current local `212/550` baseline untouched until a new baseline is explicitly accepted.
- Create a pre-change checkpoint before any authorized rebuild.
- Preserve prior SQLite schema exports, table lists, manifests, and retrieval reports.
- Never use raw Chroma or SQLite database copies as ChatGPT Project Sources.
- If evaluation regresses, stop promotion and restore the last accepted baseline.
- Hosted Vector Store deletion or expiration must follow a recorded lifecycle decision.

---

## Sources

Official OpenAI references:

- Responses migration: https://developers.openai.com/api/docs/guides/migrate-to-responses
- File Search: https://developers.openai.com/api/docs/guides/tools-file-search
- Responses API: https://developers.openai.com/api/docs/guides/responses
- Agents SDK: https://openai.github.io/openai-agents-python/
- Deprecations: https://developers.openai.com/api/docs/deprecations
- Datasets/evaluation: https://developers.openai.com/api/docs/guides/evaluation-getting-started
- Workspace Agents: https://developers.openai.com/workspace-agents

Project evidence:

- `openai_workspace_current_rag_baseline.md`
- `18-openai_workspace_post_baseline_next_actions.md`
- `openai_workspace_hybrid_retrieval_runbook.md`
- `openai_workspace_index_exclusion_policy.md`
- `WRITE_TARGET_POLICY.md`
- `database-role-map.md`
- `knowledge_bifl_toolchain_summary.md`

---

## One-line decision

Preserve the clean local `212/550` SQLite–FTS5–Chroma baseline; migrate Assistants flows incrementally to Responses; pilot OpenAI File Search only with a curated hosted corpus; place governed logic in the Agents SDK; and keep Workspace Agents thin.
