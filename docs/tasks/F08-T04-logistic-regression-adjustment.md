# F08-T04 — Estimate adjusted effect with logistic regression

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | Done |
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

- `analysis/regression.py`: naïve (`converted ~ sla_met`, `converted ~ log2_hours + no_response`) and **adjusted** logistic models (+ lead score, channel, source, size band — the DAG's adjustment set; mediators excluded), coefficients with OR and CI, average marginal effects, VIF, calibration by decile, **g-computation** of the policy "everyone answered within 30 min", bootstrap of the whole procedure (200 refits), binned functional-form check, stratification by lead-score quintile, `compare_with_truth()` and `plot_effect_comparison()`. `inference.leads_from_generated()` builds the analysis frame straight from the generator (tests, multi-seed robustness).
- **Estimates before the truth was read:** adjusted β(log2 hours) = −0.181, 95 % CI [−0.202, −0.161], OR 0.834 per doubling of (1 + hours); AME −2.0 pp per doubling; naïve β = −0.264. Calibration within ±0.7 pp in every decile. VIF ≤ 1.2 for the variables of interest; ~9 only for partner source vs partner-referral channel (collinear by design, 90 % overlap). Binned check: OR 1.00 / 0.90 / 0.59 / 0.42 for ≤ 1 h / 1-4 h / 4-24 h / > 24 h — monotone, supporting the log form. Stratifying by lead-score quintile alone shrinks the gap from 9.6 to 5.5 pp: confounding made visible. No sign reversal, so no Simpson's paradox in the strict sense.
- **Then the truth:**

  | Quantity | Estimate (95 % CI) | Truth | In CI |
  |---|---|---|---|
  | OR per doubling — naïve | 0.768 (0.753, 0.783) | 0.850 | no |
  | OR per doubling — adjusted | **0.834 (0.817, 0.851)** | 0.850 | **yes** |
  | gain for leads that missed the SLA — naïve gap | +9.63 pp (8.96, 10.30) | +3.25 | no |
  | gain for leads that missed the SLA — adjusted | +3.65 pp (3.25, 4.06) | +3.25 | no (by 0.005 pp) |
  | policy lift, all within 30 min — adjusted | +2.49 pp (2.26, 2.71) | +2.23 | no (by 0.04 pp) |

  Adjustment removes most of the bias (9.6 → 3.6 pp vs 3.2 true), but the two percentage-point CIs **narrowly miss** the truth. Candidate explanations, *not* chosen yet: (a) sampling — β̂ is 1.6 bootstrap SDs more negative than the truth and every pp effect inherits it; (b) definition — the truth averages over all 50 000 simulated leads with true response times, the analysis excludes 239 leads with corrupted times. The pre-registered multi-seed robustness check (F08-T06) will distinguish chance from systematic bias.
- Deviation D1 recorded in the plan: size-band reference category changed to `small` (a reparametrisation; it fixed misleading VIFs and changes no estimate).
- Figure fixes after review: duplicate "adjusted" labels on the pp panel and a legend coloured like one series were replaced by explicit row labels and a hand-built legend; the legend was moved off a CI.
