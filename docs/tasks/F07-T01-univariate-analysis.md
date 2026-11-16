# F07-T01 — Classify variables and describe distributions

| Field | Value |
|---|---|
| **Feature** | [F07 — Exploratory & descriptive analysis](../features/F07-exploratory-analysis.md) |
| **Status** | Done |
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

- `analysis/eda.py`: `load_leads()` (one row per lead from the marts with dimension attributes resolved; probable duplicates excluded by default — KI-01), `VARIABLES` catalogue with measurement level and role for every column, `variable_catalog()`, `frequency_table()` (absolute, relative, cumulative; ordinal order or Pareto order; missing as its own row), `describe_numeric()` (classical *and* robust statistics), `valid_response_minutes()` and `plot_distributions()`.
- **Measurement levels decided explicitly:** `lead_score` is discrete but treated as interval (101 ordered, equally spaced values); `local_hour` is discrete and *cyclic* (23 h is next to 0 h); `company_size` is a skewed count; `seniority` and `company_size_band` are ordinal, so their cumulative share is meaningful.
- **Why median and p90 for response time:** mean 477 min (8.0 h) vs median 77 min (1.3 h) — skewness 21.7, excess kurtosis 505. The mean is dominated by overnight/weekend waits and data errors. Lead score, by contrast, is symmetric (mean 50.3 ≈ median 50, skewness 0.00).
- The response-time histogram (log scale) is **multimodal**: a main mode around 1 h and secondary peaks around ~14 h and ~60 h — leads created after closing time and at weekends. That is a process effect, not noise (analysed in F07-T02).
- Figure fix after the first render: reference-line labels (median/mean/p90) overlapped; they are now staggered with a background box. A `-0.00` skewness displayed as `0.00`.
- Tests on small known inputs (MAD, ordinal ordering, missing row, excluded invalid times) and a check that every column of the SQL select has a measurement level.
