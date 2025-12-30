#!/usr/bin/env python3
"""
Evaluate two prompt-spec JSONs (Spec A vs Spec B) across 100 prompts.

Requires:
  pip install openai

Env:
  OPENAI_API_KEY=...
  MODEL_UNDER_TEST=gpt-4o        # or your preferred model
  MODEL_JUDGE=gpt-4o-mini        # cheaper judge model, or same as above

Run:
  python scripts/eval_p4_specs.py

Outputs:
  results.csv
  summary.txt
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from openai import OpenAI


# -----------------------------
# Spec loading
# -----------------------------

SPEC_A_PATH_DEFAULT = "P4_Cross_Domain_Analogy_Hybrid_Developer_v2.json"


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def spec_to_instructions(spec: dict) -> str:
    """
    Convert your JSON spec into a compact instruction string for the model.

    We keep it short and enforce headings + order.
    """
    # Minimal extraction with safe defaults
    name = spec.get("name", "P4")
    version = spec.get("version", "unknown")
    role = spec.get("role_description", "")

    # Prefer "response_format_order" if present; fall back to default
    default_order = ["Answer", "Analogy", "Steps/Code", "Test or Takeaway"]
    order = spec.get("response_format_order", default_order)

    coding = spec.get("coding_protocol", {})
    conceptual = spec.get("conceptual_protocol", {})

    coding_sections = coding.get(
        "required_sections",
        ["Pseudocode", "Code", "Analogy", "How to Run/Test"],
    )
    conceptual_sections = conceptual.get(
        "required_sections",
        ["Core Answer", "Analogy", "Actionable Insights"],
    )

    # Your user constraint: English only
    return f"""You are operating under spec: {name} v{version}.

Role:
{role}

Global required section order for non-coding:
- {order[0]}
- {order[1]}
- {order[2]}
- {order[3]}

If the request is a coding task, you MUST output exactly in this order:
- {coding_sections[0]}
- {coding_sections[1]} (FULL FILE REPLACEMENT, no diffs unless explicitly asked)
- {coding_sections[2]}
- {coding_sections[3]}

If the request is conceptual (non-coding), you MUST output:
- {conceptual_sections[0]}
- {conceptual_sections[1]}
- {conceptual_sections[2]} (2–3 items)

Constraints:
- English only.
- Professional clarity; no filler; no emojis.
- If requirements are ambiguous: state assumptions; do not invent facts.
"""


# -----------------------------
# Spec B (Enhanced v2.2) inline
# -----------------------------

SPEC_B_V22 = {
    "name": "P4 – Cross-Domain Analogy Hybrid Developer",
    "version": "2.2",
    "role_description": "You are P4, a structured reasoning and coding AI that prioritizes factual precision, reproducibility, and cross-domain analogies to improve understanding. You produce clear, runnable outputs with consistent sectioning, explicit assumptions, and verifiable steps.",
    "response_format_order": ["Answer", "Analogy", "Steps/Code", "Test or Takeaway"],
    "coding_protocol": {
        "required_sections": ["Pseudocode", "Code", "Analogy", "How to Run/Test"],
        "full_code_replacement_policy": {
            "default": "Always output a complete, self-contained code replacement (entire file/module), not partial snippets or diffs.",
            "exception": "Only output a diff/patch if the user explicitly asks for it.",
        },
    },
    "conceptual_protocol": {
        "required_sections": ["Core Answer", "Analogy", "Actionable Insights"]
    },
}


# -----------------------------
# Prompt set
# -----------------------------


@dataclass(frozen=True)
class PromptCase:
    pid: str
    category: str
    prompt: str


def build_100_prompts() -> List[PromptCase]:
    """
    Deterministic 100 prompts spanning:
      - facts (verifiable)
      - reasoning/engineering
      - metaphysics / BaZi / Feng Shui (subjective, rubric-based)
      - instruction-following / format stress tests
    """
    prompts: List[PromptCase] = []

    # 25 factual (mostly stable; avoid “current president” type questions)
    facts = [
        ("facts-01", "facts", "What is the capital of Japan?"),
        ("facts-02", "facts", "Compute 37 * 19 and show your arithmetic steps."),
        ("facts-03", "facts", "Define photosynthesis in 2 sentences."),
        ("facts-04", "facts", "What is the chemical formula for sodium chloride?"),
        ("facts-05", "facts", "State Newton’s 2nd law and give a numeric example."),
        ("facts-06", "facts", "Convert 25°C to Kelvin."),
        ("facts-07", "facts", "Explain what a byte is."),
        (
            "facts-08",
            "facts",
            "What is the difference between IPv4 and IPv6 (2-3 bullets)?",
        ),
        ("facts-09", "facts", "What is the Pythagorean theorem?"),
        ("facts-10", "facts", "Explain the greenhouse effect (non-political, scientific)."),
    ]
    # Duplicate pattern to reach 25 with variations
    for i in range(25):
        base = facts[i % len(facts)]
        pid = f"facts-{i + 1:02d}"
        prompts.append(PromptCase(pid, "facts", base[2]))

    # 25 reasoning / engineering
    reasoning_seeds = [
        "Design a checklist for diagnosing slow Wi-Fi in a house.",
        "Explain trade-offs between SQL and append-only CSV for a small app.",
        "Give a failure-mode-and-effects-analysis (FMEA) outline for an e-commerce fulfillment process.",
        "Create an OKR for improving on-time delivery and propose 3 key results.",
        "Explain how caching can cause stale reads; include a simple timeline example.",
    ]
    for i in range(25):
        pid = f"reason-{i + 1:02d}"
        prompts.append(PromptCase(pid, "reasoning", reasoning_seeds[i % len(reasoning_seeds)]))

    # 25 metaphysics / BaZi / Feng Shui (subjective; score adherence & clarity)
    metaphysics_seeds = [
        "Using BaZi concepts, explain what it means to be a Yin Wood (乙木) day master in general terms.",
        "Give a structured reading workflow for BaZi without inventing personal chart facts.",
        "How should someone approach Feng Shui decisions in a modern tropical house pragmatically?",
        "Explain the difference between Zi Wei Dou Shu and BaZi in 5 bullets.",
        "Create a neutral template for a BaZi consultation intake questionnaire.",
    ]
    for i in range(25):
        pid = f"meta-{i + 1:02d}"
        prompts.append(PromptCase(pid, "metaphysics", metaphysics_seeds[i % len(metaphysics_seeds)]))

    # 25 instruction-following / format stress tests
    stress_seeds = [
        "Write a Python script that reads a CSV and outputs summary stats. Include full file code.",
        "Rewrite this paragraph in a more formal style: 'we gonna ship soon, trust me'.",
        "Give me an answer but do NOT use any headings (this conflicts with your spec).",
        "Provide a JSON object with keys a,b,c describing your plan.",
        "Explain recursion; then give a 5-line Python example; then tests.",
    ]
    for i in range(25):
        pid = f"stress-{i + 1:02d}"
        prompts.append(PromptCase(pid, "stress", stress_seeds[i % len(stress_seeds)]))

    assert len(prompts) == 100
    return prompts


# -----------------------------
# Evaluation: format checks
# -----------------------------

REQUIRED_NONCODING = ["Answer", "Analogy", "Steps/Code", "Test or Takeaway"]
REQUIRED_CODING = ["Pseudocode", "Code", "Analogy", "How to Run/Test"]


def detect_is_coding_task(prompt: str) -> bool:
    # Simple heuristic: if user asks "write code", "python", "script", etc.
    p = prompt.lower()
    return any(k in p for k in ["python", "script", "code", "implement", "function"])


def heading_present(text: str, heading: str) -> bool:
    # Accept markdown headings or plain labels at start of a line
    pattern = rf"(?m)^\s*(#+\s*)?{re.escape(heading)}\s*$"
    return re.search(pattern, text) is not None


def order_score(text: str, headings: List[str]) -> Tuple[int, List[int]]:
    """
    Returns:
      score: number of headings found in correct relative order
      positions: list of found positions (or -1)
    """
    positions: List[int] = []
    for h in headings:
        m = re.search(rf"(?m)^\s*(#+\s*)?{re.escape(h)}\s*$", text)
        positions.append(m.start() if m else -1)
    # Score order among those present
    found = [(i, pos) for i, pos in enumerate(positions) if pos >= 0]
    in_order = 0
    last = -1
    for _, pos in found:
        if pos >= last:
            in_order += 1
            last = pos
    return in_order, positions


def format_metrics(prompt: str, output: str) -> Dict[str, float]:
    is_code = detect_is_coding_task(prompt)
    required = REQUIRED_CODING if is_code else REQUIRED_NONCODING

    present = [heading_present(output, h) for h in required]
    present_rate = sum(present) / len(required)

    in_order, positions = order_score(output, required)
    order_rate = (
        in_order / len([p for p in positions if p >= 0])
        if any(p >= 0 for p in positions)
        else 0.0
    )

    return {
        "is_coding": 1.0 if is_code else 0.0,
        "present_rate": present_rate,
        "order_rate": order_rate,
        "missing_count": float(len(required) - sum(present)),
    }


# -----------------------------
# Model calls
# -----------------------------


def call_model(
    client: OpenAI,
    model: str,
    instructions: str,
    prompt: str,
    max_output_tokens: int = 800,
) -> str:
    """
    Responses API call.
    """
    resp = client.responses.create(
        model=model,
        instructions=instructions,
        input=prompt,
        max_output_tokens=max_output_tokens,
    )
    return resp.output_text or ""


def judge_pair(
    client: OpenAI,
    judge_model: str,
    prompt: str,
    out_a: str,
    out_b: str,
) -> Dict[str, float]:
    """
    LLM-as-judge scoring 0–5 for each output across 3 axes.
    The judge is asked to be strict on section compliance + helpfulness.
    """
    rubric = """You are grading two assistant outputs for the SAME user prompt.

Score each output from 0 to 5 on:
1) Adherence: follows required section headings/order and obeys constraints.
2) Clarity: structured, concise, readable.
3) Correctness: factual/technical correctness given the prompt (if prompt is subjective, score internal consistency and avoidance of invented facts).

Return STRICT JSON only:
{
  "a": {"adherence": <0-5>, "clarity": <0-5>, "correctness": <0-5>},
  "b": {"adherence": <0-5>, "clarity": <0-5>, "correctness": <0-5>}
}
"""
    judge_in = f"{rubric}\n\nPROMPT:\n{prompt}\n\nOUTPUT A:\n{out_a}\n\nOUTPUT B:\n{out_b}\n"
    resp = client.responses.create(
        model=judge_model,
        instructions="Return JSON only. No markdown. No commentary.",
        input=judge_in,
        max_output_tokens=400,
    )
    txt = (resp.output_text or "").strip()

    # Hard parse with fallback
    try:
        data = json.loads(txt)
        return {
            "a_adherence": float(data["a"]["adherence"]),
            "a_clarity": float(data["a"]["clarity"]),
            "a_correctness": float(data["a"]["correctness"]),
            "b_adherence": float(data["b"]["adherence"]),
            "b_clarity": float(data["b"]["clarity"]),
            "b_correctness": float(data["b"]["correctness"]),
        }
    except Exception:
        # If judge fails, return zeros but keep pipeline alive
        return {
            "a_adherence": 0.0,
            "a_clarity": 0.0,
            "a_correctness": 0.0,
            "b_adherence": 0.0,
            "b_clarity": 0.0,
            "b_correctness": 0.0,
        }


# -----------------------------
# Main runner
# -----------------------------


def main() -> None:
    spec_a_path = os.environ.get("SPEC_A_PATH", SPEC_A_PATH_DEFAULT)
    model_under_test = os.environ.get("MODEL_UNDER_TEST", "gpt-4o")
    model_judge = os.environ.get("MODEL_JUDGE", "gpt-4o-mini")

    spec_a = load_json(spec_a_path)
    spec_b = SPEC_B_V22

    instr_a = spec_to_instructions(spec_a)
    instr_b = spec_to_instructions(spec_b)

    prompts = build_100_prompts()

    client = OpenAI()

    rows: List[Dict[str, object]] = []

    for i, case in enumerate(prompts, 1):
        print(f"[{i:03d}/100] {case.pid} ({case.category})")

        out_a = call_model(client, model_under_test, instr_a, case.prompt)
        out_b = call_model(client, model_under_test, instr_b, case.prompt)

        fm_a = format_metrics(case.prompt, out_a)
        fm_b = format_metrics(case.prompt, out_b)

        judge = judge_pair(client, model_judge, case.prompt, out_a, out_b)

        row = {
            "pid": case.pid,
            "category": case.category,
            "prompt": case.prompt,
            "out_a": out_a,
            "out_b": out_b,
            **{f"a_{k}": v for k, v in fm_a.items()},
            **{f"b_{k}": v for k, v in fm_b.items()},
            **judge,
        }
        rows.append(row)

        # Gentle pacing to reduce rate-limit pressure
        time.sleep(0.2)

    # Write CSV
    out_csv = "results.csv"
    fieldnames = list(rows[0].keys())
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # Summarize
    def avg(key: str, cat: Optional[str] = None) -> float:
        vals = [r[key] for r in rows if (cat is None or r["category"] == cat)]
        vals_f = [float(v) for v in vals]
        return sum(vals_f) / max(len(vals_f), 1)

    categories = sorted({r["category"] for r in rows})
    summary_lines = []
    summary_lines.append(f"MODEL_UNDER_TEST={model_under_test}")
    summary_lines.append(f"MODEL_JUDGE={model_judge}")
    summary_lines.append("")
    summary_lines.append("Overall averages:")
    for k in [
        "a_present_rate",
        "b_present_rate",
        "a_adherence",
        "b_adherence",
        "a_correctness",
        "b_correctness",
    ]:
        summary_lines.append(f"- {k}: {avg(k):.3f}")
    summary_lines.append("")
    summary_lines.append("By category:")
    for c in categories:
        summary_lines.append(f"\n[{c}]")
        for k in [
            "a_present_rate",
            "b_present_rate",
            "a_adherence",
            "b_adherence",
            "a_correctness",
            "b_correctness",
        ]:
            summary_lines.append(f"- {k}: {avg(k, c):.3f}")

    out_txt = "summary.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    print(f"\nDone.\n- Wrote {out_csv}\n- Wrote {out_txt}")


if __name__ == "__main__":
    main()