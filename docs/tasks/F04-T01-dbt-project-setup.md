# F04-T01 — Set up the dbt project

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | To Do |
| **Estimate** | 1 h |
| **Depends on** | — |
| **Branch** | `feat/F04-T01-dbt-project-setup` |

## Description

Initialise dbt with duckdb adapter and agreed folder structure.

## Steps

1. `pip install dbt-duckdb`; `dbt init` inside `dbt/`
2. `profiles.yml` in repo using `{{ env_var('LF_DB_PATH') }}`
3. `dbt_project.yml`: materialisations per folder (staging=view, marts=table)
4. `packages.yml`: `dbt_utils`; `dbt deps`
5. `_crm__sources.yml` declaring raw tables with freshness on `_loaded_at`

## Acceptance criteria

- [ ] `dbt debug` OK
- [ ] `dbt source freshness` runs

## Deliverables

- `dbt/dbt_project.yml`
- `dbt/profiles.yml`
- `dbt/packages.yml`
- `dbt/models/staging/crm/_crm__sources.yml`

## Why this matters (best practice)

Declaring *sources* lets dbt draw lineage from raw tables to dashboards and check data freshness (timeliness).

## Notes

_Add decisions, problems found and links to the PR here while working._
