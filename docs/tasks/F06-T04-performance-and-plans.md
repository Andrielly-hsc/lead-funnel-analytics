# F06-T04 — Analyse execution plans and performance

| Field | Value |
|---|---|
| **Feature** | [F06 — Analytical SQL](../features/F06-analytical-sql.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | F06-T03 |
| **Branch** | `feat/F06-T04-performance-and-plans` |

## Description

Read plans and measure the effect of physical design choices.

## Steps

1. `EXPLAIN ANALYZE` on a heavy query; annotate operators (scan, hash join, aggregate)
2. Compare: query on CSV vs on table vs on Parquet partitioned by month (`read_parquet(..., hive_partitioning=true)`)
3. Explain DuckDB zone maps vs B-tree indexes in row stores (PostgreSQL) — when indexes help OLTP vs OLAP
4. Record timings in a table

## Acceptance criteria

- [ ] Plan annotated
- [ ] Timing comparison table with ≥ 3 variants

## Deliverables

- `docs/performance.md`
- `sql/analysis/06_performance.sql`

## Why this matters (best practice)

Column stores (DuckDB, Fabric, BigQuery) rely on partition pruning and min/max statistics more than on indexes. Knowing *why* shows architecture understanding.

## Notes

_Add decisions, problems found and links to the PR here while working._
