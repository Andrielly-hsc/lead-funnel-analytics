# F08-T05 — Write the causal reasoning and limitations section

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | F08-T04 |
| **Branch** | `feat/F08-T05-causality-and-limitations` |

## Description

Be explicit about what the data can and cannot prove.

## Steps

1. Present the DAG and the adjustment set (backdoor criterion, in plain language)
2. Alternative explanations: reverse causality (agents prioritise promising leads), unmeasured confounders, selection bias
3. Representativeness: does this period/sample reflect future leads?
4. Recommendation: run a randomised experiment (A/B on routing) to confirm

## Acceptance criteria

- [ ] Section reviewed against the checklist in ARCHITECTURE §6.4

## Deliverables

- `reports/analysis_report.md` section

## Why this matters (best practice)

In real administrative data you never know the truth; recommending an experiment shows you know how to *get* causal evidence.

## Notes

_Add decisions, problems found and links to the PR here while working._
