---
source_id: oa_docs_evals
title: Evals
category: openai_docs
source_urls:
  - https://github.com/openai/evals
  - https://raw.githubusercontent.com/openai/evals/main/README.md
  - https://platform.openai.com/docs/guides/evals
  - https://github.com/openai/openai-openapi
fetched: 2026-07-12
fetch_method: curl of raw README.md + raw openapi.yaml (grepped); WebSearch cross-check (docs guide is 403-blocked)
pull_status: fetched
verify: README fetched verbatim; /evals paths confirmed present in openai-openapi spec (6 path definitions).
---

# Evals

> Provenance: "Evals" spans two distinct things sharing a name — the open-source `openai/evals` Python framework (README fetched verbatim from raw.githubusercontent.com) and the OpenAI Platform Evals API (endpoint definitions confirmed by grepping the fetched `openai-openapi/openapi.yaml`); the hosted docs guide itself is 403-blocked and was cross-checked via WebSearch only.

## What it is

Two separate surfaces, easy to conflate:

1. **`openai/evals`** — an open-source (MIT) Python framework + Git-LFS registry of benchmark evals, run locally with the `oaieval` CLI. This is the older, code-first surface.
2. **Platform Evals API / Dashboard** — a hosted product with REST endpoints (`/evals`, runs, output items) and a UI, using structured graders instead of Python. The README banner explicitly points here: "You can now configure and run Evals directly in the OpenAI Dashboard."

Both aim at the same goal — measuring how well a model / LLM system performs on a task — but the API surfaces below are not interchangeable.

## Open-source framework (openai/evals) — from fetched README

Verbatim opening definition:

> "Evals provide a framework for evaluating large language models (LLMs) or systems built using LLMs. We offer an existing registry of evals to test different dimensions of OpenAI models and the ability to write your own custom evals for use cases you care about. You can also use your data to build private evals..."

Key facts pulled directly from the README (`main`):

- **Install / run locally:** `pip install evals`; requires **Python 3.9** minimum; needs `OPENAI_API_KEY`. To develop evals, clone and `pip install -e .`.
- **Registry / data:** stored via **Git-LFS**. Populate with `git lfs fetch --all && git lfs pull` (populates pointer files under `evals/registry/data`); can fetch a single eval with `git lfs fetch --include=evals/registry/data/${your eval}`.
- **Two authoring paths:** basic / model-graded evals via **YAML + JSON data only, no code** (`docs/eval-templates.md`, `docs/build-eval.md`); custom-logic evals in Python (`docs/custom-eval.md`).
- **Completion Function Protocol** (`docs/completion-fns.md`) — for "more advanced use cases like prompt chains or tool-using agents."
- **Contribution constraint (verbatim):** "Please note that we are currently not accepting evals with custom code! While we ask you to not submit such evals at the moment, you can still submit model-graded evals with custom model-graded YAML files."
- Optional result logging to a **Snowflake** DB (`SNOWFLAKE_ACCOUNT`, `_DATABASE`, `_USERNAME`, `_PASSWORD`); W&B integration mentioned.
- **License:** MIT. Contributing means licensing eval logic + data under MIT; "OpenAI reserves the right to use this data in future service improvements."
- Starter guide: cookbook.openai.com "Getting Started with OpenAI Evals".

## Platform Evals API (create eval / runs / graders) — verify endpoints from spec

`/evals` paths **are present** in the fetched `openai-openapi/openapi.yaml` (`master`). Two OpenAPI tags exist: **`Evals`** ("Manage and run evals in the OpenAI platform.") and **`Graders`** ("Manage and run graders in the OpenAI platform."). Confirmed path + operation definitions (line numbers in fetched spec):

| Path | Method → operationId | Purpose (from spec summary) |
|------|----------------------|------------------------------|
| `/evals` | GET `listEvals` / POST `createEval` | List evals for a project / create an eval structure |
| `/evals/{eval_id}` | GET `getEval` / POST `updateEval` / DELETE `deleteEval` | Retrieve / update / delete an eval |
| `/evals/{eval_id}/runs` | GET `getEvalRuns` / POST `createEvalRun` | List runs / kick off a run |
| `/evals/{eval_id}/runs/{run_id}` | GET `getEvalRun` / POST `cancelEvalRun` / DELETE `deleteEvalRun` | Retrieve / cancel / delete a run |
| `/evals/{eval_id}/runs/{run_id}/output_items` | GET `getEvalRunOutputItems` | List per-sample graded output items |
| `/evals/{eval_id}/runs/{run_id}/output_items/{output_item_id}` | GET `getEvalRunOutputItem` | Retrieve a single output item |

**createEval** summary (verbatim from spec): "An evaluation is a set of testing criteria and the config for a data source, which dictates the schema of the data used in the evaluation. After creating an evaluation, you can run it on different models and model parameters. We support several types of graders and datasources."

**createEvalRun** summary (verbatim): "Kicks off a new run for a given evaluation, specifying the data source, and what model configuration to use to test. The datasource will be validated against the schema specified in the config of the evaluation."

**Graders** — grader `type` values seen in spec examples: `string_check`, `text_similarity`, `label_model`, `score_model` (plus a separate `/fine_tuning/alpha/graders/run` → `runGrader` endpoint for standalone grader execution). WebSearch corroborates these as the platform grader families (deterministic string check, similarity metric like rouge_l/fuzzy_match, and model-based label/score grading).

Model of the API (from spec + WebSearch): an **eval** = reusable dataset-schema + testing criteria (graders); an **eval run** = execution of that eval against a data source with a chosen model config, producing graded **output items**.

## Relevance to this repo (quality gates for relay/agent outputs)

- The **Platform Evals API** is the natural fit for automated quality gates on relay/agent outputs: define an eval once (schema + graders), then POST runs in CI against candidate model/prompt configs and read back pass/fail `output_items`. `string_check`/`text_similarity` graders suit deterministic relay checks; `label_model`/`score_model` graders suit open-ended judgment (LLM-as-judge) over agent responses.
- The **open-source framework** is heavier (Git-LFS registry, Snowflake logging, Python) and is better for offline benchmark-style regression suites than for lightweight inline gating.
- Grader semantics (eq/ilike, similarity thresholds, passing labels) map cleanly onto "does the relayed output meet criteria X" gate checks.

## Verify / TODO

- [ ] The hosted guide `platform.openai.com/docs/guides/evals` and `developers.openai.com` are **403-blocked** — grader request/response field schemas (e.g. exact `RunGraderRequest`) were not read in full, only inferred from spec examples. Confirm against live API reference when access is available.
- [ ] A third-party blog (qaskills.sh, via WebSearch) claims the hosted Evals platform is being **deprecated** (read-only ~Oct 31 2026, shutdown ~Nov 30 2026). **UNVERIFIED** — not corroborated by any official OpenAI source fetched here, and the `/evals` endpoints remain fully defined in the current spec. Do not rely on this until confirmed officially.
- [ ] Confirm current minimum Python version and whether `pip install evals` still tracks the active registry (README on `main` as of 2026-07-12 states Python 3.9).
