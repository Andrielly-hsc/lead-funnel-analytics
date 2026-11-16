# SQL pitfalls that silently produce wrong numbers

> None of these mistakes raises an error. The query runs, the dashboard renders, and
> the number is wrong. Each one is reproduced on this project's data in
> [`sql/analysis/05_pitfalls.sql`](../sql/analysis/05_pitfalls.sql); full results in
> [`reports/sql/05_pitfalls.md`](../reports/sql/05_pitfalls.md) (seed 42, 50 000 leads).

## Summary

| # | Pitfall | Wrong | Right | Error |
|---|---|---:|---:|---:|
| P1 | Null treated as zero (avg response time) | 457.0 min | 477.2 min | −4 % (team looks faster) |
| P2 | `count(*)` instead of `count(column)` | 50 000 | 45 994 | +9 % |
| P3 | `NOT IN` with a null in the subquery | **0** | 50 000 | −100 % |
| P4 | Join fan-out before summing | €902.1 M | €228.7 M | **+294 %** |
| P5 | Average of per-group averages | 18.76 % | 15.60 % | +3.2 pp |
| P6 | Business hours computed in UTC | 73.2 % | 77.4 % | −4.2 pp |
| P7 | Known duplicates not excluded | 94.83 % | 95.77 % | −0.9 pp |
| P8 | `!=` filter drops nulls | 41 388 | 45 394 | −9 % |
| P9 | Integer division (engine-dependent) | 3 | 3.5 | — |

## Why each happens and how to avoid it

### P1 — Null is not zero
A never-answered lead has **no** response time, not a response time of zero.
`coalesce(minutes, 0)` turns "missing" into "instant".
**Rule:** keep nulls; report the share of missing values as its own metric (here: the
response rate). Aggregates such as `avg()` already ignore nulls.

### P2 — `count(*)` vs `count(column)`
`count(*)` counts rows; `count(col)` counts non-null values; `count(distinct col)`
counts distinct non-null values. Decide which question you are answering.

### P3 — `NOT IN` and nulls
`x not in (a, b, null)` means `x != a and x != b and x != null`. The last comparison is
*unknown* (null), so the whole condition is never true and the query returns nothing.
**Rule:** prefer `NOT EXISTS` (or a left anti-join) whenever the subquery column can be
null — and outer-joined columns usually can.

### P4 — Join fan-out
Joining a table at one grain (lead) to a table at a finer grain (interaction) repeats
the coarse row once per fine row; any sum of a coarse measure is multiplied.
**Rule:** know the grain of every table (it is declared in each dbt model), and
aggregate to the same grain *before* joining. The reconciliation tests in dbt
(F04-T05) exist to catch exactly this.

### P5 — Average of averages
Averaging per-channel rates weights a channel with 5 000 leads the same as one with
25 000. Here the small, high-converting partner channel pulls the average up.
**Rule:** compute rates from the underlying counts (`sum(numerator) / sum(denominator)`).
The same applies to rolling rates (see `03_window_functions.sql`, Q2).

### P6 — Time zones
Timestamps are stored in UTC; business rules (opening hours, "per day") live in local
time, which in Germany is UTC+1 in winter and UTC+2 in summer.
**Rule:** store UTC, convert to local time *explicitly* for hour-of-day and calendar
logic (`created_at_local`, `dim_date` keyed on the local date).

### P7 — Known data-quality issues
Duplicate leads are never contacted, so they lower the response rate.
**Rule:** every metric definition states which known issues it excludes
(`docs/data/known_issues.md`), and every query applies the same filters.

### P8 — Inequality filters and nulls
`industry != 'retail'` is null for leads with unknown industry, and `where` keeps only
*true* rows, so those leads disappear. If they belong in the result, use
`industry is distinct from 'retail'` (or `or industry is null`).

### P9 — Integer division
`7 / 2` is `3.5` in DuckDB, but `3` in PostgreSQL and SQL Server. A conversion rate
written as `count_converted / count_all` can silently become 0 after a migration.
**Rule:** cast explicitly (`cast(x as double) / y`) in SQL meant to be portable.
