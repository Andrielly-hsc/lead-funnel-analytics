# F08-T01 — Write the analysis plan (pre-registration)

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
