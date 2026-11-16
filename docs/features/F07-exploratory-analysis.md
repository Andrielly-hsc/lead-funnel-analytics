# F07 — Exploratory & descriptive analysis

| Field | Value |
|---|---|
| **Status** | Done |
| **Priority** | Must (MoSCoW) |
| **Depends on** | [F04](F04-dimensional-model-dbt.md) |
| **Estimate** | 7 h |
| **Created** | 2026-11-15 |

## Goal

Describe the funnel rigorously: variable types, distributions, group and period comparisons, anomalies and source limitations.

## User story

> As a manager, I want to understand what is normal and what is unusual in our lead handling, so that I know where to look.

## Scope

**In scope**

- Univariate and bivariate descriptive statistics
- Group and time comparisons
- Anomaly detection (rule-based)
- Figure standards

**Out of scope**

- Predictive modelling (not needed for these questions; covered in projects 2 and 4)

## Acceptance criteria

- [x] Notebook `01_eda.ipynb` runs top-to-bottom from a clean kernel
- [x] All logic lives in `src/lead_funnel/analysis/eda.py` with tests
- [x] A 'Limitations of the source' section exists

## Tasks

| ID | Task | Estimate | Status |
|---|---|---|---|
| [F07-T01](../tasks/F07-T01-univariate-analysis.md) | Classify variables and describe distributions | 2 h | Done |
| [F07-T02](../tasks/F07-T02-group-and-period-comparison.md) | Compare groups and periods | 2 h | Done |
| [F07-T03](../tasks/F07-T03-anomalies-and-limitations.md) | Detect anomalies and document source limitations | 2 h | Done |
| [F07-T04](../tasks/F07-T04-visualisation-standards.md) | Implement figure standards | 1 h | Done |

## Syllabus topics covered

- 1.1 Data types and variables; frequency distributions; position and dispersion; exploration and visualisation; comparison of groups and periods; patterns, anomalies and source limits
- 5.1 Outliers and imbalance

## Definition of Done

- All tasks are **Done** and their acceptance criteria are met
- Code merged to `main` through a Pull Request with green CI
- Documentation (README / docs) updated
- [ARCHITECTURE.md](../ARCHITECTURE.md) conventions followed (or an ADR records the deviation)
