# OpenAI Reference Pack (personal project — simple)

Everything you need, pulled from OpenAI's GitHub and developer docs. Kept simple
on purpose: single agent + function tools + file search. No guardrails/handoffs
yet (add later if the project grows).

Python note: `openai` 3.x needs **Python 3.10+**; you run 3.12/3.13. Pinned
`openai>=3.0,<4.0`. Exception: `examples/agents/` stays on `openai>=2.45,<3.0`
because `openai-agents` (through 0.20.0) still requires `openai<3` — install it
in its own virtualenv.

---

## 1. Official GitHub repos

| Repo | What it is | Link |
|---|---|---|
| `openai/openai-python` | **Official Python SDK** — the client you import | https://github.com/openai/openai-python |
| `openai/openai-agents-python` | **Agents SDK** — build agents (tools, run loop) | https://github.com/openai/openai-agents-python |
| `openai/openai-cookbook` | **Examples & guides** (notebooks) | https://github.com/openai/openai-cookbook |
| `openai/plugins` | Codex plugins (successor to `openai/skills`) | https://github.com/openai/plugins |

## 2. API Platform & Developer docs

| Resource | Use | Link |
|---|---|---|
| Platform dashboard | API keys, projects, **Vector Stores**, usage/billing | https://platform.openai.com |
| Developer docs (home) | All API guides | https://developers.openai.com |
| Quickstart | First API call | https://developers.openai.com/api/docs/quickstart |
| Models | Model ids, context, pricing | https://developers.openai.com/api/docs/models |
| Function calling | Tools/schemas | https://developers.openai.com/api/docs/guides/function-calling |
| File search (RAG) | Vector-store grounding | https://developers.openai.com/api/docs/guides/tools-file-search |
| Embeddings | text-embedding-3-* | https://developers.openai.com/api/docs/guides/embeddings |
| Agents SDK guide | Define & run agents | https://developers.openai.com/api/docs/guides/agents |
| Agents SDK (Python API ref) | Class/method reference | https://openai.github.io/openai-agents-python/ |

## 3. Minimal Python quickstarts

**Official SDK — one call:**
```python
from openai import OpenAI
client = OpenAI()                        # reads OPENAI_API_KEY from env
r = client.responses.create(model="gpt-5.1", input="Say hi in one line.")
print(r.output_text)
```

**Official SDK — embeddings:**
```python
v = client.embeddings.create(model="text-embedding-3-small", input=["hello", "world"])
print(len(v.data[0].embedding))          # 1536
```

**Agents SDK — one agent, no guardrails/handoffs:**
```python
pip install openai-agents
```
```python
from agents import Agent, Runner, function_tool

@function_tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

agent = Agent(name="Assistant", instructions="You are helpful.", tools=[multiply])
print(Runner.run_sync(agent, "What is 6 times 7?").final_output)
```

**Agents SDK — add file search (RAG) when you have a vector store:**
```python
from agents import Agent, Runner, FileSearchTool
agent = Agent(name="KB", instructions="Answer from the knowledge base.",
              tools=[FileSearchTool(vector_store_ids=["vs_..."], max_num_results=5)])
```

## 4. Cookbook notebooks most useful for this project

(GitHub path — open as `github.com/openai/openai-cookbook/blob/main/<path>`)

**Function calling / tools**
- `examples/How_to_call_functions_with_chat_models.ipynb`
- `examples/How_to_call_functions_for_knowledge_retrieval.ipynb`
- `examples/responses_api/responses_api_tool_orchestration.ipynb` (multi-tool + RAG)

**File search / RAG**
- `examples/File_Search_Responses.ipynb` (RAG on PDFs via File Search)

**Embeddings (your indexing/search work)**
- `examples/Using_embeddings.ipynb`
- `examples/Question_answering_using_embeddings.ipynb`
- `examples/Semantic_text_search_using_embeddings.ipynb`
- `examples/Embedding_long_inputs.ipynb` (chunking long text)

**Agents SDK**
- `examples/agents_sdk/parallel_agents.ipynb`
- `examples/agents_sdk/building_reliable_agents_memory_compaction.ipynb`
- `examples/Build_a_coding_agent_with_GPT-5.1.ipynb`

## 5. Keep-it-simple path (personal project)

```
1. openai-python  → call the model / make embeddings          (you have this)
2. one Agent + @function_tool                                 (relay_agent.py)
3. add FileSearchTool once a Vector Store exists              (agent_pro.py)
4. (later, only if needed) handoffs, guardrails, sessions
```

Skip enterprise pieces (guardrails, multi-agent handoffs, governance) until the
single-agent version actually does useful work.

## Workspace Recovery And Source Hygiene

Dated status checkpoints, storage/source policies, and inventory manifests for the
OpenAI Workspace Project (see `docs/status/`, `docs/policies/`, `reference/manifests/`):

- `docs/status/openai_workspace_current_retrieval_eval_state_20260721.md`
- `docs/status/openai_workspace_post_cleanup_project_source_verification_20260721.md`
- `docs/status/source_manifest_preflight_v5_final_consistency_closure_20260813_221526.md`
- `docs/status/archive_intake_audit_20260814.md`
- `docs/policies/WRITE_TARGET_POLICY.md`
- `docs/policies/database-role-map.md`
- `docs/policies/openai_workspace_index_exclusion_policy.md`
- `docs/policies/p4_index_pointer.md`
- `reference/manifests/manifest_20260814.json`
- `reference/manifests/archive_members_20260814.json`

## OpenAI Upstream Reference Pins

Dated commit pins for referenced OpenAI upstream repositories (pointer-only; not vendored):

- `reference/openai/upstream-clone-pins-20260814.md`
- `reference/manifests/openai_upstream_pins_20260814.json`
- `reference/openai/upstream-clone-pins-20260815.md` (batch 2: sites, node, cli, evals, tiktoken, codex, python, codex-action, plugins, developers-for-claude, developers-for-cursor, retrieval-plugin)
- `reference/manifests/openai_upstream_pins_20260815.json`
