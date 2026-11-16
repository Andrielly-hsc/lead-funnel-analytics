# F06-T03 — Document common SQL pitfalls

| Field | Value |
|---|---|
| **Feature** | [F06 — Analytical SQL](../features/F06-analytical-sql.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | F06-T02 |
| **Branch** | `feat/F06-T03-sql-pitfalls` |

## Description

Demonstrate errors that silently produce wrong numbers.

## Steps

1. `count(*)` vs `count(col)` with nulls
2. `NOT IN` with a null in the subquery returns nothing
3. Join fan-out: joining leads to interactions then summing amounts
4. Averages of averages vs weighted averages
5. `avg(minutes)` including leads never answered (null ≠ 0)
6. Each case: wrong query, result, correct query, result

## Acceptance criteria

- [ ] At least 5 pitfalls with reproducible examples

## Deliverables

- `sql/analysis/05_pitfalls.sql`
- `docs/sql_pitfalls.md`

## Why this matters (best practice)

Interviewers love these — and they are exactly the “errors of interpretation in queries” listed in your syllabus.

## Notes

_Add decisions, problems found and links to the PR here while working._
