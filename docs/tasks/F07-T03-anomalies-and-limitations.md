# F07-T03 — Detect anomalies and document source limitations

| Field | Value |
|---|---|
| **Feature** | [F07 — Exploratory & descriptive analysis](../features/F07-exploratory-analysis.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F07-T02 |
| **Branch** | `feat/F07-T03-anomalies-and-limitations` |

## Description

Separate data errors from genuine extreme behaviour.

## Steps

1. IQR and robust z-score (median/MAD) on response time
2. Classify: impossible (negative), implausible (> 30 days), legit extremes
3. Write 'Limitations of the source': selection (only leads that reached the CRM), measurement (clock skew), missingness mechanisms (MCAR/MAR)

## Acceptance criteria

- [ ] Anomaly counts reconcile with injected issues
- [ ] Limitations section ≥ 5 points

## Deliverables

- `notebooks/01_eda.ipynb` section
- `docs/data/known_issues.md` updated

## Why this matters (best practice)

Recognising the limits of administrative data (data collected for operations, not research) is exactly what your syllabus item 3.2 asks for.

## Notes

- `eda.py` additions: `iqr_fences()`, `robust_z()` (median/MAD, scaled by 1.4826), `outlier_method_comparison()`, `classify_response_times()` (impossible / implausible / extreme but plausible / normal), `detection_vs_injected()`, `missingness_by()` and `plot_anomalies()`.
- **Outliers are not errors.** On the right-skewed response time, the Tukey IQR fence on raw minutes flags **16 %** of leads — almost all legitimate night and weekend waits. The same fence on log-minutes, a robust z > 3.5 on log-minutes and the domain rule "> 30 days" each flag **95 leads = exactly the injected wrong-import-date errors**. Lesson: transform skewed data before applying symmetric outlier rules, and use *domain* rules to call something an error.
- Rule-based flags vs the generator's injection log: precision 1.0 and recall 1.0 for both clock-skew (144) and extreme-delay (95) errors.
- **Missingness mechanisms with evidence:** `company_size` is missing for 25.0 % of web-form leads vs ~3 % elsewhere, with non-overlapping CIs → *not* MCAR (MAR, explained by channel); `industry` is missing ~8 % in every channel with overlapping CIs → consistent with MCAR. Ratio computed from the data (8×), not typed into the caption.
- New section **"Limitations of the source"** in `docs/data/known_issues.md` (L1-L7): selection, non-designed treatment (confounding), measurement error, non-random missingness, external validity, process-imposed structure, unobserved drivers — each with its consequence for the analysis.
- My own mistake caught by the test suite: I first wrote the expected IQR fences of 1..8 as (−3.25, 12.25); the correct values are (−2.5, 11.5). The code was right, the test expectation was wrong.
