# F02-T03 — Simulate funnel events with the causal effect

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | To Do |
| **Estimate** | 4 h |
| **Depends on** | F02-T02 |
| **Branch** | `feat/F02-T03-funnel-simulation` |

## Description

Simulate response times, interactions and conversion according to the DAG.

## Steps

1. Response time ~ log-normal, depends on channel, hour-of-day, agent workload and (negatively) on lead quality
2. Interactions: first response + 0–5 follow-ups, event types `call`, `email`, `meeting`
3. Conversion ~ Bernoulli(logit⁻¹(β₀ + β_q·quality + β_rt·hours_to_response + β_ch·channel))
4. Opportunities: amount ~ log-normal for converted leads
5. Save the true coefficients to `data/raw/_ground_truth.json`

## Acceptance criteria

- [ ] Naïve conversion gap (SLA vs non-SLA) is *larger* than the true causal effect (confounding works)
- [ ] Logistic regression with the true covariates recovers β_rt within its 95 % CI

## Deliverables

- `src/lead_funnel/generator/funnel.py`
- `data/raw/_ground_truth.json`

## Why this matters (best practice)

This is how you *demonstrate* confounding and Simpson's paradox with evidence instead of definitions — a strong talking point in interviews.

## Notes

_Add decisions, problems found and links to the PR here while working._
