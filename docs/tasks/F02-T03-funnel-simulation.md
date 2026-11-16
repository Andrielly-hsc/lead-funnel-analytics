# F02-T03 — Simulate funnel events with the causal effect

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | Done |
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

- First response: leads created outside business hours (Mon-Fri 08:00-18:00 Europe/Berlin) wait for the next opening (`numpy.busday_offset`); then a log-normal working time depending on channel, agent seniority, lead score (the confounding path) and daily team workload.
- Conversion: logistic model of `ConversionParams`. For every lead the generator also computes the **counterfactual** probability under the policy "answered within 30 minutes" — something real data never shows.
- `statsmodels` was added as a dependency (needed now to validate effect recovery, and in F08 anyway).
- Validation with seed 42, 50 000 leads (2.8 s):

  | Quantity | Value |
  |---|---|
  | conversion rate | 15.6 % |
  | leads never answered | 4.2 % |
  | median hours to first response | 1.28 h (p90 14.8 h, p99 60 h) |
  | **naïve SLA gap** (met vs missed) | **8.8 pp** |
  | **true effect** on leads that missed the SLA | **3.2 pp** |
  | true policy lift (all leads answered in 30 min) | 2.2 pp |
  | `beta_log2_hours` true / adjusted estimate (95 % CI) | −0.1625 / −0.181 (−0.2015, −0.1609) ✔ |
  | `beta_log2_hours` without confounders | −0.265 (biased) |

  The naïve comparison almost triples the real effect: confounding works as designed (acceptance criterion met). The adjusted CI contains the truth.
- Consistency checks: every responded lead's earliest interaction equals its first response; no opportunity opens before the first response; ~2.1 interactions per responded lead.
- **pandas pitfall:** `Series.to_numpy()` on a timezone-aware column returns an *object* array of `Timestamp`s, which cannot be added to `timedelta64`. Convert with `.dt.tz_convert(None)` (naive UTC) first.
