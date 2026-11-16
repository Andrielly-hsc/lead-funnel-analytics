# F04-T04 — Build dimension models (incl. SCD Type 2)

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | To Do |
| **Estimate** | 3 h |
| **Depends on** | F04-T03 |
| **Branch** | `feat/F04-T04-dimension-models` |

## Description

Create conformed dimensions with surrogate keys.

## Steps

1. `dim_date` via `dbt_utils.date_spine` (day grain, weekday, ISO week, month, is_weekend)
2. `dim_agent` from a dbt **snapshot** (strategy `check` on `team`) → `valid_from`, `valid_to`, `is_current`
3. `dim_channel`, `dim_lead_source` (small dimensions)
4. Surrogate keys with `dbt_utils.generate_surrogate_key`

## Acceptance criteria

- [ ] `dim_agent` has >1 row for agents that changed team
- [ ] PK unique + not_null for all dims

## Deliverables

- `dbt/snapshots/agents_snapshot.sql`
- `dbt/models/marts/dim_*.sql`

## Why this matters (best practice)

SCD Type 2 answers “which team was the agent in *when the lead was handled*?” — without it, history is silently rewritten.

## Notes

_Add decisions, problems found and links to the PR here while working._
