# F08-T03 — Analyse correlations and ANOVA

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
