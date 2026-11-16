# F07-T01 — Classify variables and describe distributions

| Field | Value |
|---|---|
| **Feature** | [F07 — Exploratory & descriptive analysis](../features/F07-exploratory-analysis.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | — |
| **Branch** | `feat/F07-T01-univariate-analysis` |

## Description

Start with the basics, done properly.

## Steps

1. Table classifying every mart column: nominal, ordinal, discrete, continuous; role (ID, dimension, measure)
2. Frequency tables (absolute, relative, cumulative) for categoricals
3. Mean, median, mode, std, IQR, MAD, skewness, kurtosis for numerics; explain why median/p90 for response time (right-skewed)
4. Histograms with log scale for response time

## Acceptance criteria

- [ ] Variable typing table in the notebook
- [ ] Choice of central-tendency measure justified

## Deliverables

- `src/lead_funnel/analysis/eda.py`
- `notebooks/01_eda.ipynb`

## Why this matters (best practice)

Choosing median over mean for skewed data is a small decision that signals statistical maturity.

## Notes

_Add decisions, problems found and links to the PR here while working._
