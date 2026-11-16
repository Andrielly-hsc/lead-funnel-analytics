# F05-T01 — Profile raw data

| Field | Value |
|---|---|
| **Feature** | [F05 — Data quality & profiling](../features/F05-data-quality-profiling.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | — |
| **Branch** | `feat/F05-T01-profiling` |

## Description

Describe each raw table before cleaning.

## Steps

1. `quality/profiling.py`: per column — type, % null, distinct count, min/max, top values, pattern checks
2. Use DuckDB `SUMMARIZE` as a fast baseline
3. Output `reports/quality/profile_<table>.md`
4. `lead-funnel profile` sub-command

## Acceptance criteria

- [ ] Profile produced for every raw table

## Deliverables

- `src/lead_funnel/quality/profiling.py`
- `reports/quality/`

## Why this matters (best practice)

Profiling first, cleaning second: you can't define rules for data you haven't looked at.

## Notes

_Add decisions, problems found and links to the PR here while working._
