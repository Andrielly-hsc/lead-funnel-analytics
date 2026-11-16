# F06-T03 — Document common SQL pitfalls

| Field | Value |
|---|---|
| **Feature** | [F06 — Analytical SQL](../features/F06-analytical-sql.md) |
| **Status** | Done |
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

- `05_pitfalls.sql`: nine mistakes that run without error but return wrong numbers, each as **one row with the wrong and the right result side by side** on the real warehouse; explained in `docs/sql_pitfalls.md` (why it happens + the rule that prevents it).
- Measured impact (seed 42): join fan-out inflates the pipeline value from €228.7 M to **€902.1 M (+294 %)**; `NOT IN` with a null in the subquery returns **0** instead of 50 000; average of channel rates 18.8 % vs true 15.6 %; `coalesce(null, 0)` makes the team look 4 % faster; UTC instead of local hours misclassifies 4.2 pp of leads; `!=` silently drops the 4 006 leads with unknown industry.
- Several pitfalls tie back to earlier design decisions: declared grain + reconciliation tests (P4), null semantics in `int_leads__first_response` (P1), `created_at_local` (P6), the known-issues register (P7).
- Tooling: the ANSI `cast()` in P9 is intentional (portability is the point), so the sqlfluff fixer is stopped with an inline `-- noqa: CV11` (the exact format matters: extra text after the rule code disables it). `run_sql.py` now ignores trailing comments when detecting the end of a statement — the noqa comment had made it drop the last query.
