---
source_id: oa_docs_prompt_guidance
title: Prompt Guidance
category: openai_docs
source_urls:
  - https://platform.openai.com/docs/guides/prompt-engineering
  - https://developers.openai.com/api/docs/guides/reasoning-best-practices
  - https://developers.openai.com
  - https://github.com/openai/openai-cookbook
  - https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/gpt4-1_prompting_guide.ipynb
  - https://cookbook.openai.com/examples/gpt4-1_prompting_guide
fetched: 2026-07-12
fetch_method: Fetched the openai-cookbook README (raw.githubusercontent.com) and the GPT-4.1 prompting guide notebook (raw.githubusercontent.com/openai/openai-cookbook/.../gpt4-1_prompting_guide.ipynb) directly. platform.openai.com and developers.openai.com are 403-blocked to automated fetch, so their guidance (prompt-engineering guide, reasoning-best-practices) was confirmed via WebSearch.
pull_status: fetched
verify: Re-open source_urls in a browser; cookbook notebooks and reasoning-best-practices drift as model families change (GPT-5.x, o-series).
---

# Prompt Guidance

> Provenance: Core techniques below are quoted/paraphrased from the OpenAI Cookbook GPT-4.1 prompting guide (fetched this session) and the OpenAI API prompt-engineering + reasoning-best-practices guides (web-verified; those doc hosts are 403-blocked here).

## What it is
OpenAI's prompt guidance is split across three official surfaces: the platform
**Prompt engineering** guide (`platform.openai.com/docs/guides/prompt-engineering`),
the **Reasoning best practices** guide (`developers.openai.com/api/docs/guides/reasoning-best-practices`),
and hands-on **Cookbook** guides (e.g. the GPT-4.1 and GPT-5 prompting guides on
`github.com/openai/openai-cookbook`). The central framing: there are two model
families — **GPT models** (e.g. GPT-4.1) and **reasoning / o-series models**
(o3, o4-mini) — that are "not better or worse, just different" and need
different prompting styles. GPT models want precise, explicit instructions;
reasoning models want high-level goals and room to think.

## Core techniques (from official guidance / cookbook)
From the **GPT-4.1 Cookbook guide** (fetched):

- **Agentic reminders** — three system-prompt reminders raised OpenAI's internal
  SWE-bench Verified score ~20%:
  - *Persistence*: "keep going until the user's query is completely resolved,
    before ending your turn and yielding back to the user."
  - *Tool-calling*: "If you are not sure about file content or codebase structure
    ... use your tools ... do NOT guess or make up an answer."
  - *Planning* (optional): "You MUST plan extensively before each function call,
    and reflect extensively on the outcomes of the previous function calls."
- **Use the API `tools` field, not injected tool text** — parsing tools via the
  request field (vs. pasting descriptions into the prompt) measured ~2% better
  and keeps the model "in distribution." Name tools clearly; put detailed
  behavior in the `description`; put usage examples in an `# Examples` section of
  the system prompt, not crammed into the description.
- **Literal instruction-following** — GPT-4.1 follows instructions more closely
  and literally than predecessors. Structure with a "Response Rules" /
  "Instructions" section, add specific sub-sections (e.g. "Sample Phrases"), use
  ordered step lists for workflows. When debugging: later instructions win on
  conflict; add a demonstrating example; reserve ALL-CAPS for genuine emphasis.
- **Induced chain-of-thought** — GPT-4.1 is *not* a reasoning model but responds
  to "think step by step" prompting; explicit planning induction improved
  SWE-bench pass rate ~4%. Tradeoff: more output tokens = higher cost/latency.
- **Recommended prompt skeleton**: Role and Objective -> Instructions (+ sub-categories)
  -> Reasoning Steps -> Output Format -> Examples -> Context -> Final instructions /
  step-by-step thinking prompt.
- **Delimiters**: start with **Markdown** section titles; **XML** works well and
  is good for wrapping many documents with metadata; **JSON** is verbose,
  needs escaping, and tested poorly for large document sets. For doc collections,
  `ID: 1 | TITLE: ... | CONTENT: ...` performed well.
- **Long context** (up to 1M tokens): place key instructions at **both the start
  and end** of the context (or above it if only once); performance degrades as
  retrieval/reasoning complexity rises. Example grounding instruction: "Only use
  the documents in the provided External Context to answer the User Query. If you
  don't know the answer based on this context, you must respond 'I don't have the
  information needed to answer that.'"

From the platform **Prompt engineering** guide (web-verified): write clear
instructions, provide reference text, split complex tasks into simpler subtasks,
give the model time to "think," use few-shot examples, and iterate/refine.

## Reasoning-model vs standard-model prompting notes (verify current)
Web-verified from **Reasoning best practices**:

- **Keep it simple and direct.** Reasoning models perform best with high-level
  guidance; "trust the model's inherent reasoning abilities." Over-instructing
  can *hurt* them.
- **Avoid "think step by step" prompts** on o-series — explicit CoT instructions
  may not help and can hinder, since the model already reasons internally.
  (Opposite of GPT-4.1, where CoT prompting helps.)
- **Developer vs system message**: since `o1-2024-12-17`, reasoning models take
  a **developer message** (the "system rules / business logic", like a function
  definition) instead of a system message; user messages are the "arguments."
- **Markdown suppression**: since `o1-2024-12-17`, API reasoning models avoid
  markdown output by default; put the literal string **"Formatting re-enabled"**
  on the first line of the developer message to opt back in.
- **Be specific about the end goal / success criteria** and state explicit
  constraints; let the model iterate until it meets them.
- **Reasoning effort levels** (o3 / o4-mini): `low` (clear-spec coding, synthesis
  Q&A), `medium` (default; multi-step analysis), `high` (hard math, proofs,
  multi-file codegen).
- o-series strengths: planning/strategy over ambiguous inputs, math, science,
  engineering, legal/financial expert-level tasks.

## Relevance to this repo (relay prompt patterns, agents)
This repo is a ChatGPT-Team relay that forwards to OpenAI (`app/api/forward_openai.py`,
`app/api/tools_api.py`, `app/manifests/tools_manifest.json`). Practical takeaways:

- **Route prompting by model family.** If the relay targets an o-series model,
  strip injected CoT scaffolding and pass goals via a developer message; for
  GPT-4.x/5.x targets, keep explicit instructions and optional CoT.
- **Declare tools via the API `tools` field**, not by pasting tool docs into the
  relayed prompt — matches OpenAI's measured best practice and keeps our
  `tools_manifest.json` the single source of truth.
- **Agentic reminders** (persistence + tool-calling + planning) belong in any
  agent/system prompt the relay composes for multi-step tasks.
- **Long-context relays**: repeat critical instructions at start and end of the
  forwarded context; prefer Markdown/XML framing over JSON for bundled docs.
- Honor **"Formatting re-enabled"** and developer-message semantics when relaying
  to reasoning models so downstream markdown/formatting behaves as expected.

## Verify / TODO
- Reconcile against live `platform.openai.com/docs/guides/prompt-engineering` and
  `developers.openai.com/.../reasoning-best-practices` in a browser (both 403 here).
- Pull the **GPT-5 prompting guide** (`developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide`)
  and the **o3/o4-mini prompting guide** for family-specific deltas — not fully
  captured here.
- Confirm current default reasoning-effort behavior and any new model families
  (GPT-5.x) vs. the guidance above; effort-level names/defaults drift.
- Cross-check "Formatting re-enabled" and developer-message rules still apply to
  the newest reasoning models.
