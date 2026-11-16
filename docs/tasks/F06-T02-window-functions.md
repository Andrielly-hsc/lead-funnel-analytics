# F06-T02 — Use window functions for rankings and trends

| Field | Value |
|---|---|
| **Feature** | [F06 — Analytical SQL](../features/F06-analytical-sql.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F06-T01 |
| **Branch** | `feat/F06-T02-window-functions` |

## Description

Show fluency with the most asked-about SQL feature in interviews.

## Steps

1. Agent ranking per week (`dense_rank`)
2. Rolling 4-week conversion (`avg … over (rows between 3 preceding and current row)`)
3. Time between touches (`lag`)
4. Weekly cohorts: conversion by week-of-creation × weeks-since-creation

## Acceptance criteria

- [ ] Each query explained in a comment

## Deliverables

- `sql/analysis/03_window_functions.sql`
- `sql/analysis/04_cohorts.sql`

## Why this matters (best practice)

Window functions compute per-row values *without collapsing rows*, which is what most real reporting needs.

## Notes

- `03_window_functions.sql`: weekly agent ranking (`dense_rank` + `qualify`, minimum 20 leads per agent-week), rolling 4-week conversion, days between consecutive touches (`lag` + `row_number`), monthly running total and share of the year (`sum() over (order by)` / `sum() over ()`), each agent vs their team average (`avg() over (partition by team)`). Named `window w4 as (...)` avoids repeating the frame.
- `04_cohorts.sql`: weekly cohorts of Q1 2025 with cumulative conversion at 0/1/2/4 weeks, and monthly cohorts with conversion, 7-day conversion and median days to opportunity.
- **Two analytical traps made explicit in the queries:** (1) a rolling *rate* must be the ratio of rolling **sums**, not the rolling average of weekly rates (the "wrong" column is kept next to the right one for contrast); (2) `qualify` exists because `where` runs *before* window functions are computed. Note: `qualify` is DuckDB/Snowflake/BigQuery syntax; in PostgreSQL wrap the query in a CTE and filter outside.
- Cohort caveat documented in the file: in a live CRM the newest cohorts are **right-censored** (not enough time to convert yet), so cohorts must be compared at ages all of them have reached.
- Findings: most conversions happen within the first week (conv_week_0 ≈ 11-13 % of a ≈ 15-17 % final rate); median 3.5 days to opportunity, stable across months; follow-ups are spaced ~1.3 days apart (median).
- `run_sql.py` no longer prints years with a thousands separator (2,025 → 2025).
