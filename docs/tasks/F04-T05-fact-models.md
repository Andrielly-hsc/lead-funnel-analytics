# F04-T05 — Build fact models

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | To Do |
| **Estimate** | 3 h |
| **Depends on** | F04-T04 |
| **Branch** | `feat/F04-T05-fact-models` |

## Description

Create the two facts with declared grain.

## Steps

1. `fct_leads` (accumulating snapshot): one row per lead with milestone timestamps, response minutes, `sla_met`, `is_converted`, amount, FKs
2. `fct_interactions` (transaction): one row per interaction with FKs to lead, agent (point-in-time join on SCD2 validity), date
3. Relationship tests from facts to every dimension

## Acceptance criteria

- [ ] `relationships` tests pass
- [ ] Reconciliation: sum of converted leads == rows in `stg_crm__opportunities`

## Deliverables

- `dbt/models/marts/fct_*.sql`
- `_marts__models.yml`

## Why this matters (best practice)

Declaring the grain in the YAML description prevents the most common analytics bug: fan-out joins that multiply rows and inflate sums.

## Notes

_Add decisions, problems found and links to the PR here while working._
