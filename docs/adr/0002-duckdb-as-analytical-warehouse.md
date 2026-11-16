# ADR-0002: Use DuckDB as the analytical warehouse

- **Status:** Accepted
- **Date:** 2026-11-15

## Context

We need a SQL warehouse with window functions, native CSV/JSON/Parquet reading and good analytical performance, that runs on a laptop and in CI with zero setup. Options: PostgreSQL (needs a server/Docker), SQLite (row store, weak analytics), cloud warehouses (cost, accounts), DuckDB.

## Decision

Use **DuckDB** (embedded, columnar, OLAP) stored in a single file `data/warehouse/lead_funnel.duckdb`.

## Consequences

- + Zero infrastructure; CI runs the full pipeline
- + Columnar engine teaches modern OLAP concepts (zone maps, vectorised execution) used by Fabric, Snowflake, BigQuery
- − Single writer; not a multi-user server
- − Index concepts of row stores (PostgreSQL B-trees) must be explained separately (done in F06-T04)
- Migration path: dbt models are mostly ANSI SQL and can move to Postgres/Fabric Warehouse by switching adapter
