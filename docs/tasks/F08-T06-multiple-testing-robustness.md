# F08-T06 — Correct for multiple testing and run robustness checks

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F08-T05 |
| **Branch** | `feat/F08-T06-multiple-testing-robustness` |

## Description

Make results stable and honest across segments.

## Steps

1. Segment-level tests (by team, channel) with Holm and Benjamini–Hochberg corrections
2. Sensitivity: different SLA thresholds (30/60/120 min), excluding anomalies, different seeds
3. Stability table: does the conclusion change?

## Acceptance criteria

- [ ] Corrected vs uncorrected p-values shown
- [ ] Conclusion stable across ≥ 3 robustness variants (or instability explained)

## Deliverables

- `inference.py` functions
- notebook section

## Why this matters (best practice)

Testing 20 segments at α = 0.05 yields ~1 false positive by chance. Correction is not optional when you slice data.

## Notes

- Done **before T05** (plan deviation D3): the causal write-up has to explain these results.
- `analysis/robustness.py`: `segment_tests()` (H1 in 19 segments with Holm and Benjamini-Hochberg), `sensitivity_table()` (plan §7 checks 1-3), `seed_study()` + `seed_study_summary()` (check 4: independent synthetic datasets), `plot_seed_study()`.
- **Multiple testing:** all 19 segment tests stay significant after both corrections (smallest effect: social +5.8 pp) — the result does not hinge on the correction. Holm controls the chance of *any* false positive (FWER), BH the expected *share* of false discoveries (FDR) and is less strict. Plan deviation D2: the plan said 17 tests; the family has 19 (counting error).
- **Sensitivity of the adjusted analysis:** OR per doubling stays 0.834-0.845 in every variant; the gain for leads that missed the SLA is 2.9 / 3.6 / 4.7 pp for SLA 30 / 60 / 120 min, 3.4 pp with the 239 error leads included. **Not robust in one variant:** business hours only — 1.9 pp, below the +2 pp threshold — because inside business hours missed-SLA leads are answered within a few hours, so faster response gains less. Reported as instability, as the plan requires.
- **Multi-seed study (20 clean datasets × 50 000 leads, ~1 min):** mean β −0.1618 vs true −0.1625 (error +0.0007 ± 0.0023); effect on missed-SLA leads 3.254 vs 3.269 pp; policy lift 2.205 vs 2.215 pp; β CI coverage 18/20 = 90 % (consistent with 95 % at n = 20). **Conclusion for T04:** the adjusted estimator is unbiased; the seed-42 intervals that narrowly missed the truth are sampling variation — exactly what a 95 % CI does about once in 20 datasets.
- **Two bugs found:** (1) a `RuntimeWarning` exposed that, with error leads included, negative response times produced `log2` of negative numbers (NaN) in the counterfactual — hours are now clipped at 0; (2) a `ConvergenceWarning` in a 4 000-lead test run was **quasi-complete separation** (zero conversions among 164 never-answered leads → the coefficient runs to −∞). `regression.fit()` now refuses non-converged models with an explicit `ModelDidNotConverge` error instead of returning unreliable estimates; a test reproduces the separation.
