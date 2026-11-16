# F08-T04 — Estimate adjusted effect with logistic regression

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | To Do |
| **Estimate** | 3 h |
| **Depends on** | F08-T03 |
| **Branch** | `feat/F08-T04-logistic-regression-adjustment` |

## Description

Show how confounding biases the naïve estimate.

## Steps

1. Model A (naïve): `converted ~ sla_met`
2. Model B (adjusted): `+ lead_score + C(channel) + C(source) + C(company_size_band)`
3. Interpret odds ratios with CIs; average marginal effects in pp
4. Diagnostics: VIF, calibration plot, influential points
5. Table: naïve vs adjusted vs **true** effect from `_ground_truth.json`
6. Demonstrate Simpson's paradox in one segment if present

## Acceptance criteria

- [ ] Adjusted estimate's CI contains the true effect
- [ ] Naïve bias quantified

## Deliverables

- `src/lead_funnel/analysis/regression.py`
- `reports/figures/effect_comparison.svg`

## Why this matters (best practice)

This single table — naïve vs adjusted vs truth — is the most convincing artefact of the whole project.

## Notes

_Add decisions, problems found and links to the PR here while working._
