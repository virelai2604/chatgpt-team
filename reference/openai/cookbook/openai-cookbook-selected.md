---
source_id: gh_openai_cookbook
title: openai/openai-cookbook — selected notebooks (Responses / File Search / Agents / Evals)
category: cookbook_selected
source_urls:
  - https://github.com/openai/openai-cookbook
  - https://raw.githubusercontent.com/openai/openai-cookbook/main/registry.yaml
  - https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/File_Search_Responses.ipynb
  - https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/responses_api/responses_example.ipynb
  - https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/agents_sdk/parallel_agents.ipynb
  - https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/evaluation/use-cases/responses-evaluation.ipynb
retrieved_at: 2026-07-16
fetch_method: WebFetch of registry.yaml + the four selected notebooks (all listed above) on raw.githubusercontent.com (GitHub is fetchable)
pull_status: fetched
verify: notebooks evolve; re-pull the specific .ipynb before building against it, and confirm current model IDs / tool schemas
---

# openai/openai-cookbook — selected notebooks

> Provenance: `fetched` (2026-07-16) from the repo `registry.yaml` and four
> notebooks (GitHub raw is fetchable). Curated to the four topics this repo cares
> about — **Responses API, File Search, Agents SDK, Evals** — not the whole cookbook.

## What it is

Official OpenAI example code + guides (Python-first, principles language-agnostic).
Navigable at `cookbook.openai.com`; every example is indexed in the repo's
`registry.yaml` (title + `path` under `examples/`). MIT-licensed. This snapshot
pulls only the notebooks relevant to the relay/BIFL stack.

## Selected notebooks (the four tracks)

### 1. File Search — `examples/File_Search_Responses.ipynb`
**Doing RAG on PDFs using File Search in the Responses API.** Distilled:

```python
# 1) hosted vector store
vector_store = client.vector_stores.create(name=store_name)

# 2) upload + attach files (OpenAI chunks/embeds/indexes automatically)
file_response = client.files.create(file=open(file_path, "rb"), purpose="assistants")
client.vector_stores.files.create(vector_store_id=vector_store.id, file_id=file_response.id)

# 3) single call = retrieval + generation via the file_search tool
response = client.responses.create(
    input=query,
    model="gpt-4o-mini",
    tools=[{
        "type": "file_search",
        "vector_store_ids": [vector_store_id],
        "max_num_results": k,
    }],
)
```
No external vector DB / manual chunking. The notebook validates retrieval quality
(Recall@5 / MRR / MAP over a generated QA set). **Most directly relevant to BIFL's
`bifl.search`/`fetch`.**

### 2. Responses API — `examples/responses_api/responses_example.ipynb`
**Web Search and State with the Responses API.** Distilled:

```python
# basic
response = client.responses.create(model="gpt-4o-mini", input="tell me a joke")
text = response.output[0].content[0].text

# chain turns with server-side state
response_two = client.responses.create(
    model="gpt-4o-mini",
    input="tell me another",
    previous_response_id=response.id,   # continue; reuse the same id to fork/branch
)

# hosted web_search tool (model decides when to call it; output carries URL citations)
response = client.responses.create(
    model="gpt-4o",
    input="What's the latest news about AI?",
    tools=[{"type": "web_search"}],
)
```
Also multimodal input (`input_text` + `input_image`) in one request. State is managed
server-side via `previous_response_id` (no manual history threading).

### 3. Agents SDK — `examples/agents_sdk/parallel_agents.ipynb`
**Parallel Agents with the OpenAI Agents SDK (Python).** Distilled:

```python
# Pattern A — asyncio fan-out over independent agents
responses = await asyncio.gather(
    *(Runner.run(agent, review_text) for agent in parallel_agents)
)
# results labeled + concatenated → meta-agent synthesizes

# Pattern B — agents-as-tools, planner decides order
meta_agent = Agent(
    tools=[features_agent.as_tool(...), pros_cons_agent.as_tool(...)],
    model_settings=ModelSettings(parallel_tool_calls=True),
)
```
Primitives: `Agent`, `Runner.run()`, `.as_tool()`, `ModelSettings(parallel_tool_calls=True)`.
Same primitive set as the JS SDK snapshot (`agents-sdk/openai-agents-js.md`).

### 4. Evals — `examples/evaluation/use-cases/responses-evaluation.ipynb`

> ⚠️ **DEPRECATION — provenance `web_verified` (2026-07-16), NOT `fetched`.**
> The official OpenAI pages below **403 to automated fetch** in this environment (same as
> the rest of `developers.openai.com`), so these dates are **web-verified from
> official-domain results, not a verbatim fetched snapshot** — browser-confirm to promote
> to `fetched`.
>
> OpenAI is **deprecating the Evals platform**: **read-only 2026-10-31**, **shutdown
> 2026-11-30**. **Datasets** is the recommended path for new work; a named
> **"Moving from OpenAI Evals to Promptfoo"** migration guide exists. **Do NOT build fresh
> relay-grading automation on the Evals API** — treat the snapshot below as a record of
> the retiring pattern; target **Datasets** for anything new.
>
> Official OpenAI sources (all on openai.com domains; all 403 automated fetch here):
> - Read-only/shutdown dates: `https://developers.openai.com/api/docs/deprecations`
>   · `https://community.openai.com/t/deprecation-notice-evals-will-be-shut-down-on-november-30th-2026/1385537`
> - Datasets replacement: `https://developers.openai.com/api/docs/guides/evaluation-getting-started`
> - Promptfoo migration: `https://developers.openai.com/cookbook/examples/evaluation/moving-from-openai-evals-to-promptfoo`
> - Evals platform status: `https://developers.openai.com/api/docs/guides/evals`

**Evaluate new models against stored Responses API logs (Evals API — retiring).** Distilled:

```python
# define the eval over logged responses
eval_obj = client.evals.create(
    name="Code QA Eval",
    data_source_config={"type": "logs"},        # reference stored responses
    testing_criteria=[{
        "type": "score_model",
        "model": "o3",                            # grader model
        "input": [ ... system/user message objects ... ],
        "range": [1, 7],
        "pass_threshold": 5.5,
    }],
)

# run A: score existing logged responses
client.evals.runs.create(eval_id=eval_obj.id, data_source={"type": "responses"})

# run B: regenerate with a candidate model, reusing logged inputs
client.evals.runs.create(
    eval_id=eval_obj.id,
    data_source={"model": "gpt-4.1-mini", "type": "...", "item_reference": "..."},
)
# results dashboard at run.report_url
```
Key idea: reuse **production logs** as the eval dataset instead of hand-building one.
The *technique* is still sound; the *Evals API surface shown here is retiring* (see the
deprecation banner) — port the same idea onto **Datasets** for new relay-grading work.

## Other notable entries in `registry.yaml` (pointers, not pulled)

- Responses: `responses_api/responses_api_tool_orchestration.ipynb` (multi-tool RAG routing),
  `responses_api/reasoning_items.ipynb`.
- Agents: `agents_sdk/multi-agent-portfolio-collaboration/…`, `agents_sdk/evaluate_agents.ipynb`,
  `agents_sdk/agent_improvement_loop.ipynb`, `deep_research_api/introduction_to_deep_research_api_agents.ipynb`.
- Evals: the full `examples/evaluation/use-cases/` family (regression, tools, web-search,
  structured-outputs, MCP evaluation), `evaluation/Building_resilient_prompts_using_an_evaluation_flywheel.md`.
- Workspace agents: `examples/chatgpt/workspace_agents/workspace-agents-api-trigger.ipynb`
  (see also `workspace-agents/workspace-agent-trigger-runs.md` — the official page snapshot).

## Relevance to this repo (ChatGPT Team Relay / BIFL)

- **File Search notebook** is the closest template for `bifl.search`/`fetch` (hosted
  vector store + `file_search` tool, no external DB).
- **Responses API** state model (`previous_response_id`) + hosted `web_search` mirror
  what the relay proxies.
- **Agents parallel** patterns port to the Node path (`agents-sdk/openai-agents-js.md`).
- **Evals-over-logs** is a good pattern for grading relay output without a bespoke
  dataset — but implement it on **Datasets**, since the Evals API is retiring (shutdown
  2026-11-30). The stored-logs-as-eval-set idea carries over; the API surface changes.

## Verify / TODO

- Re-pull the specific `.ipynb` before implementing — notebooks pin model IDs
  (`gpt-4o-mini`, `o3`, `gpt-4.1-mini`) and tool schemas that move.
- `data_source` shape for regeneration runs (`item_reference`) is abbreviated here;
  confirm exact fields from the live notebook when wiring an eval.
- **Before building any new eval automation:** confirm the current **Datasets** API
  (the Evals platform goes read-only 2026-10-31, shuts down 2026-11-30) — do not pin new
  work to the deprecated `client.evals.*` surface.
