# F06-T01 — Write funnel KPI queries

| Field | Value |
|---|---|
| **Feature** | [F06 — Analytical SQL](../features/F06-analytical-sql.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | — |
| **Branch** | `feat/F06-T01-funnel-kpi-queries` |

## Description

Core KPIs from the marts.

## Steps

1. Volume, conversion rate, median/p90 minutes to response, SLA compliance by channel/source/team/week
2. Funnel: created → responded → meeting → converted with step conversion
3. Use CTEs, `filter (where …)` aggregates, `group by rollup` for totals

## Acceptance criteria

- [ ] Queries run via `duckdb data/warehouse/lead_funnel.duckdb < file.sql`

## Deliverables

- `sql/analysis/01_funnel_kpis.sql`
- `sql/analysis/02_sla_compliance.sql`

## Why this matters (best practice)

Readable SQL (CTEs with meaningful names) is reviewed and reused; nested subqueries rarely are.

## Notes

- `sql/analysis/01_funnel_kpis.sql` (overall KPIs, KPIs by channel with `group by rollup`, nested funnel, leads that skipped stages) and `02_sla_compliance.sql` (SLA by team × channel via the point-in-time agent key, weekly ISO trend, SLA by local hour). Every file has a header: question, grain, author, assumptions (duplicates excluded — KI-01; invalid response times excluded — KI-02).
- **`scripts/run_sql.py`** runs every file on a read-only connection and writes `reports/sql/<file>.md` (question, SQL, result table), so results are reviewable on GitHub. `--check` runs them in the CI e2e job, so a schema change that breaks a query fails the build.
- **Funnel pitfall found:** counting each stage independently made *converted* (7 799) larger than *meeting held* (7 783) — a step conversion of 100.2 %. Funnel stages must be **nested** (each stage only counts leads that passed all previous ones). Q4 reports the 16 converted leads that were never answered, which need a business explanation rather than silently breaking the funnel.
- **Findings (seed 42, duplicates excluded):** response rate 95.8 %, SLA rate 41.6 %, median first response 77 min (p90 15 h), conversion 15.6 %. Phone meets the SLA 71 % of the time, e-mail 18 %. Leads created between 18:00 and 07:00 local time have an SLA rate of **0 %**: nobody is working, so the 60-minute target is structurally unreachable for ~7 000 leads a year — an operational finding (and an instrument-like variable for F08).
- Style: sqlfluff enforced dbt-style SQL (one target per line, explicit aliases, `stage` is a reserved word → `funnel_stage`). Window functions `lag` / `first_value` compute step and cumulative conversion without self-joins.
