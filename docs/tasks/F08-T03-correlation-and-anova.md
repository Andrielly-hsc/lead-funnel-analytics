# F08-T03 — Analyse correlations and ANOVA

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F08-T02 |
| **Branch** | `feat/F08-T03-correlation-and-anova` |

## Description

Quantify relationships between continuous and categorical variables.

## Steps

1. Pearson vs Spearman between lead_score, response time, touches (why Spearman for skewed data)
2. One-way ANOVA: interaction duration by channel; check normality (Q-Q, Shapiro on subsample) and homoscedasticity (Levene)
3. Welch ANOVA / Kruskal-Wallis as alternatives; η² / ω² effect sizes; Tukey HSD post-hoc

## Acceptance criteria

- [ ] Assumption checks shown before each test
- [ ] Effect sizes reported

## Deliverables

- `inference.py` functions
- notebook section

## Why this matters (best practice)

Checking assumptions and having a fallback test is what “interpretation of results” means in practice.

## Notes

- `inference.py` additions: `correlation_table()` (Pearson + Spearman with p-values), `one_way_anova()` (group stats, Shapiro on a 500-point subsample per group, Levene/Brown-Forsythe, classic F, **Welch** F, Kruskal-Wallis, η², ω², Tukey HSD), `anova_summary()`, `load_calls()`, `plot_qq()` (residuals raw vs log).
- **Correlations (answered leads):** lead score vs hours to response — Pearson −0.04, **Spearman −0.18**. The skew of response time hides the relation from Pearson; ranks reveal it. Lead score vs number of touches: +0.42 (agents work good leads harder).
- **H2a — log10 response time ~ channel:** Levene p ≈ 0 → Welch ANOVA; F = 2 028, p ≈ 0, **η² = 0.134** (channel explains 13 % of the variance). Reject H0. Kruskal-Wallis agrees.
- **H2b — call duration ~ channel:** Levene p = 0.35 → classic ANOVA; F = 0.99, **p = 0.40**, η² = 0.0001; Tukey: no pair differs. Do **not** reject — the correct answer, because the generator draws call durations independently of channel. A well-behaved null result is as much a part of a sound analysis as a positive one.
- **Assumptions:** Shapiro rejects normality everywhere — expected: at thousands of points it flags negligible deviations, so Q-Q plots are the primary check. The Q-Q figure shows raw-scale residuals far from normal (skewness 3.2) and log-scale residuals much closer (0.7) but still bimodal (night/weekend waits) — hence Welch plus a Kruskal-Wallis cross-check rather than trusting the classic F alone.
- Test-design lesson: a unit test first asserted "equal population variances → classic ANOVA", but Levene rejected by chance for that seed (it does in ~5 % of samples). Changing the seed until it passes would be p-hacking the test; the test now checks the *decision rule* (Welch iff Levene rejects).
