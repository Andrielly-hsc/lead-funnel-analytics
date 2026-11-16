# F06-T02 — Use window functions for rankings and trends

| Field | Value |
|---|---|
| **Feature** | [F06 — Analytical SQL](../features/F06-analytical-sql.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
