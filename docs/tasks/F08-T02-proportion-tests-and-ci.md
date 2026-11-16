# F08-T02 — Test conversion difference with CIs and effect sizes

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | F08-T01 |
| **Branch** | `feat/F08-T02-proportion-tests-and-ci` |

## Description

Answer H1 with several complementary methods.

## Steps

1. Two-proportion z-test and χ² test; Wilson CI per group
2. Effect sizes: risk difference, relative risk, odds ratio, Cohen's h
3. Bootstrap CI (10 000 resamples) for the difference as a distribution-free check
4. Explain Type I/II errors and what the p-value does *not* mean

## Acceptance criteria

- [ ] Results table with estimate, CI, p, effect size
- [ ] Practical significance discussed against the plan's threshold

## Deliverables

- `src/lead_funnel/analysis/inference.py`
- `notebooks/02_inference.ipynb`

## Why this matters (best practice)

With 50 000 leads almost any difference is “significant”. Effect size and practical relevance are what managers actually need.

## Notes

_Add decisions, problems found and links to the PR here while working._
