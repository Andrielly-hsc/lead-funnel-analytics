# F06 — Analytical SQL

| Field | Value |
|---|---|
| **Status** | In Progress |
| **Priority** | Must (MoSCoW) |
| **Depends on** | [F04](F04-dimensional-model-dbt.md) |
| **Estimate** | 8 h |
| **Created** | 2026-11-15 |

## Goal

Answer the descriptive business questions with well-structured SQL, and show awareness of SQL pitfalls and performance.

## User story

> As a support manager, I want funnel and SLA KPIs by team and week, so that I can steer staffing.

## Scope

**In scope**

- KPI queries with CTEs and aggregations
- Window functions
- Documented SQL pitfalls
- Execution plans and performance

**Out of scope**

- Stored procedures
- Access-control administration (mentioned conceptually only)

## Acceptance criteria

- [ ] Each query in `sql/analysis/` has a header comment: question, grain, author, assumptions
- [ ] Results of KPI queries reconcile with dashboard numbers
- [ ] Pitfalls document shows wrong vs right query with results

## Tasks

| ID | Task | Estimate | Status |
|---|---|---|---|
| [F06-T01](../tasks/F06-T01-funnel-kpi-queries.md) | Write funnel KPI queries | 2 h | Done |
| [F06-T02](../tasks/F06-T02-window-functions.md) | Use window functions for rankings and trends | 2 h | To Do |
| [F06-T03](../tasks/F06-T03-sql-pitfalls.md) | Document common SQL pitfalls | 2 h | To Do |
| [F06-T04](../tasks/F06-T04-performance-and-plans.md) | Analyse execution plans and performance | 2 h | To Do |

## Syllabus topics covered

- Eng 2.1 Filters, joins, aggregations, subqueries, CTEs, window functions
- Eng 2.2 Indexes, execution plans and performance; nulls, duplicates, misinterpretation errors

## Definition of Done

- All tasks are **Done** and their acceptance criteria are met
- Code merged to `main` through a Pull Request with green CI
- Documentation (README / docs) updated
- [ARCHITECTURE.md](../ARCHITECTURE.md) conventions followed (or an ADR records the deviation)
