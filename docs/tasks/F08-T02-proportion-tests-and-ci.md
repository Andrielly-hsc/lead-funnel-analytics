# F08-T02 — Test conversion difference with CIs and effect sizes

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | Done |
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

- `analysis/inference.py`: `analysis_frame()` (plan §2 exclusions; never-answered leads kept with `no_response`), `two_proportion_test()` (pooled z-test, χ², Wilson CI per group, **Newcombe** CI for the difference, relative risk, odds ratio, Cohen's *h*), `sla_conversion_test()`, `bootstrap_diff_ci()`, `proportion_test_table()`. Every result carries estimate + CI + p-value + effect size, and two flags: statistically significant and **practically relevant** (CI entirely beyond the pre-registered +2 pp).
- **H1 result (naïve association, seed 42, 49 761 leads):** conversion 21.2 % (SLA met, n = 20 736) vs 11.6 % (missed, n = 29 025): **+9.63 pp, 95 % CI [8.96, 10.30]**, z = 29.2, p ≈ 10⁻¹⁸⁷, RR 1.83, OR 2.05, Cohen's *h* 0.26 (small). Same picture in business hours (+9.63 pp) and among answered leads only (+8.78 pp).
- Cross-checks: the percentile bootstrap (10 000 resamples) reproduces the Newcombe interval to two decimals; z² equals χ² exactly (851.64), as theory says for a 2×2 table without continuity correction.
- Bootstrap trick: resampling n Bernoulli outcomes and counting successes *is* a Binomial(n, p̂) draw, so `rng.binomial` gives the non-parametric bootstrap without materialising 10 000 × 50 000 resamples.
- Interpretation recorded for T04/T05: this +9.6 pp is an **association**. The plan expects confounding by lead quality, so it is not the effect of answering faster.
- Type I/II errors: α = 0.05 bounds false alarms; power ≈ 1 for the +2 pp effect (plan §5) makes a Type II error on that size negligible. A p-value is the probability of data at least this extreme *if H0 were true* — not the probability that H0 is true, nor the size or importance of the effect.
- `scipy` declared as a direct dependency (used directly; previously only transitive via statsmodels).
