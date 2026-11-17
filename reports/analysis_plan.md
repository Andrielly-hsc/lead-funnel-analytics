# Analysis plan (pre-registration)

> **Status:** fixed before any inferential result was computed. This file is committed
> on its own (`docs(F08-T01)`), *before* the inference code exists — the git history is
> the evidence. Any later deviation is listed in the section *Deviations* at the end,
> with its reason; nothing is silently changed.
>
> Author: Andrielly-hsc · Date: 2026-11-16 · Data: seed 42, 50 000 leads, warehouse
> `marts.fct_leads` (feature F04), descriptive results from F06/F07.

## 1. Questions

| # | Question | Type |
|---|---|---|
| Q1 | Do leads answered within the SLA (≤ 60 min) convert at a different rate than leads that are not? | descriptive inference |
| Q2 | Does handling differ across channels (response time, call duration)? | descriptive inference |
| Q3 | After adjusting for lead quality, channel, source and company size, is faster response associated with higher conversion — and how much would a faster-response policy add? | causal (under stated assumptions) |

## 2. Population and exclusions

- **Unit:** one lead (`fct_leads`), created in 2025.
- **Excluded:** probable duplicates (known issue KI-01) — never contacted, not separate people.
- **Excluded from the primary analysis:** leads with an **invalid** response time
  (clock skew, KI-02) and **implausible** delays > 30 days (KI-03) — 239 leads whose true
  response time is unknown. They are put back in a robustness check (§7).
- **Never-answered leads** stay in: for Q1 they count as "SLA missed"; for Q3 they get
  their own indicator (`no_response`).
- **Secondary population:** leads created during business hours (Mon-Fri 08:00-18:00
  local), where the SLA is actionable (limitation L6).

## 3. Hypotheses, tests and estimands

| # | H0 | Test | Effect size reported |
|---|---|---|---|
| H1 | conversion(SLA met) = conversion(SLA missed) | two-proportion z-test (two-sided) and χ²; 95 % CIs: Wilson per group, Newcombe for the difference; bootstrap CI (10 000 resamples) as a distribution-free check | risk difference (pp), relative risk, odds ratio, Cohen's *h* |
| H2a | mean log response time is equal across channels | one-way ANOVA after checking normality (Q-Q, Shapiro on a subsample) and equal variances (Levene); **Welch ANOVA** if variances differ; Kruskal-Wallis as non-parametric check; Tukey HSD post-hoc | η², ω² |
| H2b | mean call duration is equal across channels | same procedure | η², ω² |
| H3 | β(log2(1 + hours to first response)) = 0 in the **adjusted** logistic model | Wald test on the coefficient | odds ratio per doubling of (1 + hours) with 95 % CI; average marginal effects (pp) |

Correlations (Pearson and Spearman) between lead score, response time and number of
touches are reported descriptively, with a note on why Spearman suits skewed data.

### Models for H3

- **Naïve:** `converted ~ sla_met` and `converted ~ log2_hours + no_response`.
- **Adjusted (primary):** `converted ~ log2_hours + no_response + lead_score_z + C(channel) + C(lead_source) + C(company_size_band)`.
- **Adjustment set** from the causal DAG ([`docs/data/causal_dag.md`](../docs/data/causal_dag.md)):
  lead score, channel, source, company-size band. **Not** adjusted for: number of touches
  or meetings (mediators — they happen after the first response).
- **Functional form:** `log2(1 + hours)` as stated in the DAG document (assumption A1).
  A binned-response-time model is reported as a check of this assumption.
- **Policy estimand (g-computation):** mean predicted conversion if every lead were answered
  within 30 minutes, minus the mean predicted conversion as observed; 95 % CI by
  non-parametric bootstrap of the whole fitting procedure.
- **Diagnostics:** VIF of covariates, calibration (predicted vs observed by decile).

## 4. Decision rules

- **α = 0.05**, two-sided, for every primary test.
- **Minimum effect of practical interest:** **+2 percentage points** of conversion
  (≈ +1 000 opportunities a year at 50 000 leads). A statistically significant effect
  smaller than this is reported as *not practically relevant*.
- Effects are always reported as estimate + 95 % CI; a p-value alone is never a result.

## 5. Power (computed from the overall conversion rate only)

Baseline: overall conversion 15.6 % (published descriptive figure, F06). Group sizes
(counts only): 20 736 leads with SLA met, 29 120 without.

| Difference to detect | Cohen's *h* | n per group for 80 % power | Power with our n |
|---|---:|---:|---:|
| +1 pp | 0.027 | 21 200 | 0.85 |
| **+2 pp (minimum of interest)** | 0.054 | 5 429 | **≈ 1.00** |
| +3 pp | 0.080 | 2 468 | ≈ 1.00 |

The smallest difference detectable with 80 % power is **≈ 0.95 pp**. Consequence: with
this sample almost any real difference will be *statistically* significant, so the
practical threshold (§4) and the effect size carry the decision.

## 6. Multiple comparisons

Segment-level H1 tests (by channel, source, team, company-size band — 17 tests) are
exploratory and corrected with **Holm** (family-wise error) and **Benjamini-Hochberg**
(false discovery rate); both corrected and uncorrected p-values are shown.

## 7. Robustness checks (pre-specified)

1. SLA threshold 30 / 60 / 120 minutes.
2. Including the 239 leads with invalid or implausible response times (as observed).
3. Business-hours population only.
4. Different random seeds of the generator (sampling variability of the whole pipeline).
5. Binned response time instead of `log2(1 + hours)`.

A conclusion is called **robust** if its direction and practical relevance hold in all
checks; otherwise the instability is reported and explained.

## 8. What is compared with the truth

Because the data is synthetic, `data/raw/_ground_truth.json` holds the true coefficient
(β = ln 0.85 per doubling of 1 + hours) and the true policy effects. They are used **only
after** the estimates are computed, to show the bias of naïve methods — never to choose a
model.

## Deviations

| # | Change | Reason | Impact on results |
|---|---|---|---|
| D1 | Reference category of `company_size_band` set to `small` instead of the alphabetical default (`enterprise`). | The default reference holds only 3 % of leads, which inflated the VIFs of the other size dummies (up to 8) and made the diagnostics misleading. | None on fit, predictions or the response-time coefficient — a reparametrisation of the same model. |
| D2 | §6 said "17 tests"; the family has **19** (4 channels + 6 sources + 4 teams + 5 size bands incl. `unknown`). | Counting error in the plan; the segments themselves are unchanged. | Corrections are applied to all 19 tests (slightly more conservative than planned). |
| D3 | Execution order: robustness (T06) was run before the written causal discussion (T05). | The discussion has to explain the robustness results (seed-42 CIs narrowly missing the truth). | None on any estimate. |
