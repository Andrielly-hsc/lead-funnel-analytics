# F04-T06 — Document models and publish lineage

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | To Do |
| **Estimate** | 1 h |
| **Depends on** | F04-T05 |
| **Branch** | `feat/F04-T06-docs-and-lineage` |

## Description

Make the warehouse self-explanatory.

## Steps

1. Descriptions for every model and column (use `{% docs %}` blocks for shared definitions)
2. Add an `exposures.yml` for the dashboard and the report
3. `dbt docs generate`; screenshot of lineage graph to `reports/figures/`

## Acceptance criteria

- [ ] 100 % models and mart columns documented

## Deliverables

- `dbt/models/**/_*.yml`
- `dbt/models/exposures.yml`
- lineage screenshot

## Why this matters (best practice)

dbt docs act as a lightweight *data catalogue*. Exposures show which consumers break if a model changes (impact analysis).

## Notes

_Add decisions, problems found and links to the PR here while working._
