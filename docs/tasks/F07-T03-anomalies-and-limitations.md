# F07-T03 — Detect anomalies and document source limitations

| Field | Value |
|---|---|
| **Feature** | [F07 — Exploratory & descriptive analysis](../features/F07-exploratory-analysis.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
