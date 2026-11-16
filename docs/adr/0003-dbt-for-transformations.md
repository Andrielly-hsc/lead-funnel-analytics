# ADR-0003: Use dbt Core for SQL transformations

- **Status:** Accepted
- **Date:** 2026-11-15

## Context

Transformations could be written as Python (pandas) scripts or as SQL files run by hand. We want versioned, testable, documented transformations with lineage — the norm in analytics engineering.

## Decision

Use **dbt Core** with the `dbt-duckdb` adapter, following the dbt Labs project structure (staging → intermediate → marts).

## Consequences

- + Tests, docs, lineage and dependency ordering for free
- + Most requested analytics-engineering skill in job ads
- + SQL stays close to what BI developers read
- − Another tool to learn (Jinja templating)
- Incremental models are **not** used: data volume (≤ 1 M rows) rebuilds in seconds; full rebuilds are simpler and always consistent
