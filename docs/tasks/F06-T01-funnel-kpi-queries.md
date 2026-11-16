# F06-T01 — Write funnel KPI queries

| Field | Value |
|---|---|
| **Feature** | [F06 — Analytical SQL](../features/F06-analytical-sql.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
