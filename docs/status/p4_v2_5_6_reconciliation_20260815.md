# P4 Reconciliation — v2.3.3 → v2.5.6 (2026-08-15)

Reconciles the repository's P4 protocol artifact to the active **v2.5.6** package
and retires the superseded v2.3.3 file.

## Decision

- **Active spec is now v2.5.6.** The full developer JSON and system prompt are
  committed to the repo (this is a public repository; committing the full spec
  was an explicit choice).
- **v2.3.3 is removed** from the repo. Its history remains recoverable via git;
  the renewal report classifies older versions as rollback/source baselines.
- The eval harness default (`scripts/eval_p4_specs.py`, `SPEC_A_PATH_DEFAULT`)
  now points at the v2.5.6 JSON.

## Committed (canonical)

| File | SHA-256 |
|---|---|
| `P4_Cross_Domain_Analogy_Hybrid_Developer_v2_5_6.json` | `2f3386ccdfe8211878dcb8a92271527b94dbea9844cad6f27db2f7cb64d27bc0` |
| `P4_system_prompt_v2_5_6.txt` | `da6250187aea183e174e0e1b8b1f1aa86292c8fbb693e5a4228d84b839ae0b43` |

Spec `name`: `P4_Cross_Domain_Analogy_Hybrid_Developer_v2_5_6`;
internal `version`: `2.5.6-gpt-5.5-agent-skills-renewed`.

## Not committed (evidence / provenance only)

Per the source-hygiene policy (`docs/policies/p4_index_pointer.md`,
`openai_workspace_index_exclusion_policy.md`), scoring output, nested archives,
and repack reports stay out of the repo. Recorded here for provenance
(source: `README_v2_5_6_renewal_report.zip`, uploaded 2026-08-15):

| File | SHA-256 | Reason excluded |
|---|---|---|
| `P4_v2_5_6_matrix_rescore_100.csv` | `41d1b13f1b5958f60fcb60b9ac6464a9e09a3a5a80480e12ab97f11b0dda870d` | Generated eval scoring output |
| `P4_v2_5_6_score_summary.json` | `a45dc95f2790a843a268d1cc3aaa6d3cb59e5e3af3ee1e5b0960ef5f08aa5e6e` | Generated eval scoring output |
| `p4-response-protocol.zip` | `6705d1473361253ea55e4ba9cfb3fd2f740aa7e90f4635e4a5a5ea0770713a9b` | Nested archive (never vendored) |
| `README_v2_5_6_renewal_report.md` | `dd276a6c905d885bfa697c790dbb50cb27d8f5251f09df05ce7a82315c612aab` | Report (distilled below) |
| `README_synced_skill_package.md` | `9ac81c90cc9c6ab7447973eaff5753180e7ce33cddf79c79c944ce7bef8beb10` | Report |
| `P4_skill_repack_report.json` | `1a3a114badd17a4639913fd9c7c5270d59a1eb05b25182fb8cd9f8b049e15fa0` | Repack report |
| `manifest_final_skill.jsonl` | `fbafefa0be06bd410abadf1bc3c1b35ccd4d1335dd31f2f02eb630d2ab5966d4` | Skill manifest |
| `P4_custom_instruction_compact_v2_5_6.txt` | `51b2315f74ba26a689ce07d3c4835d9afc059b3931360401e676747ebf747302` | Compact variant of committed prompt |
| `P4_system_prompt_v2_5_6_8000char_compact.txt` | `74cb642a3cbcf0fd18b6b58f9b3e6b7d8556460230bc55fe82a1143e085a69d7` | Compact variant of committed prompt |

## Renewal score (from the report)

Static **artifact-readiness** rescore over 30 matrices: **99.32 / 100**
(`pass_static_artifact_gate`). This is explicitly **not** a live GPT-5.5
API/latency/cost benchmark — matrix M12 stays below 100 for that reason.

## Secret / exposure review

Extracted set scanned before commit: **no secrets, no API keys, no emails.**
Only benign signals present (metaphysics domain terms `BaZi`/`Feng Shui`, and a
public GitHub URL `github.com/virelai2604/agent-skills` in the spec's
`references`). The full methodology is intentionally public in this repo.
