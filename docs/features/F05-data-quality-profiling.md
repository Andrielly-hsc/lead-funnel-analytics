# F05 — Data quality & profiling

| Field | Value |
|---|---|
| **Status** | In Progress |
| **Priority** | Must (MoSCoW) |
| **Depends on** | [F03](F03-ingestion-raw-layer.md), [F04](F04-dimensional-model-dbt.md) |
| **Estimate** | 10 h |
| **Created** | 2026-11-15 |

## Goal

Measure data quality explicitly across the six standard dimensions and handle duplicates with awareness of matching risks.

## User story

> As a data owner, I want a quality scorecard, so that I know how far I can trust each KPI.

## Scope

**In scope**

- Profiling of raw tables
- dbt generic and singular tests
- Quality scorecard (6 dimensions)
- Duplicate and near-duplicate detection; false-match risk analysis

**Out of scope**

- Full record-linkage ML model (that is project 5)

## Acceptance criteria

- [ ] Scorecard reports completeness, uniqueness, validity, consistency, accuracy, timeliness per table
- [ ] Detected issue rates are compared with injected ground truth (precision/recall of detection)
- [ ] Known accepted issues documented in `docs/data/known_issues.md`

## Tasks

| ID | Task | Estimate | Status |
|---|---|---|---|
| [F05-T01](../tasks/F05-T01-profiling.md) | Profile raw data | 2 h | Done |
| [F05-T02](../tasks/F05-T02-dbt-tests.md) | Add generic and singular dbt tests | 2 h | Done |
| [F05-T03](../tasks/F05-T03-quality-scorecard.md) | Build the six-dimension quality scorecard | 3 h | To Do |
| [F05-T04](../tasks/F05-T04-dedup-and-linkage.md) | Detect near-duplicates and assess false-match risk | 3 h | To Do |

## Syllabus topics covered

- Eng 5.2 Completeness, consistency, validity, uniqueness, accuracy, timeliness
- Eng 5.3 Profiling, deduplication, record linkage, enrichment
- Eng 5.4 Reconciliation of sources
- Eng 5.5 Risks of incorrect matches between people/entities
- 5.1 Missing values, inconsistencies, duplicates, outliers

## Definition of Done

- All tasks are **Done** and their acceptance criteria are met
- Code merged to `main` through a Pull Request with green CI
- Documentation (README / docs) updated
- [ARCHITECTURE.md](../ARCHITECTURE.md) conventions followed (or an ADR records the deviation)
