# F08-T01 — Write the analysis plan (pre-registration)

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | Done |
| **Estimate** | 1 h |
| **Depends on** | — |
| **Branch** | `feat/F08-T01-analysis-plan` |

## Description

Fix hypotheses and decisions before seeing results.

## Steps

1. H1: conversion(SLA met) > conversion(SLA missed). H2: handling duration differs across channels. H3: effect of response time persists after adjusting for lead quality, channel, source
2. α = 0.05, two-sided; minimum effect of practical interest (e.g. +2 pp conversion)
3. Power analysis: required n per group for MDE (statsmodels `NormalIndPower`)
4. Commit as `docs: add analysis plan` before task F08-T02

## Acceptance criteria

- [ ] Plan exists in git history before inference code

## Deliverables

- `reports/analysis_plan.md`

## Why this matters (best practice)

Pre-registration protects against p-hacking — testing until something is significant. It's standard in science and increasingly in product analytics (A/B testing).

## Notes

- `reports/analysis_plan.md` committed **alone and before any inference code**: questions, population and exclusions, hypotheses with tests and effect sizes, models and adjustment set (from the causal DAG; mediators explicitly *not* adjusted for), decision rules (α = 0.05, minimum effect of interest +2 pp), multiple-comparison policy, five robustness checks, and how the ground truth may be used (only after estimating, never to choose a model). A *Deviations* section records any later change.
- **Power analysis** (statsmodels `NormalIndPower`, Cohen's *h*): with ~20 700 vs ~29 100 leads, the smallest difference detectable at 80 % power is ≈ 0.95 pp; the +2 pp effect of interest has power ≈ 1. Consequence written into the plan: almost any real difference will be statistically significant, so practical relevance and effect sizes decide.
- **Method care:** my first power run used the conversion rate of the *SLA-missed group* as baseline — that already looks at the outcome by treatment group. It was redone with the overall conversion rate (15.6 %, a descriptive figure already published in F06); only group *counts* are used otherwise.
