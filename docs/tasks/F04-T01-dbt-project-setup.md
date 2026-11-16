# F04-T01 — Set up the dbt project

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | Done |
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
6. Switch `.sqlfluff` to `templater = dbt` and add `sqlfluff-templater-dbt` + `dbt-duckdb` as `additional_dependencies` of the sqlfluff pre-commit hook

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

- Dependency: `dbt-duckdb` (resolved dbt-core 1.12.7, dbt-duckdb 1.11.1, keeping DuckDB 2.0). pip-tools downgraded two transitive pins (`pathspec`, `python-dateutil`) to satisfy dbt's ranges.
- `dbt/dbt_project.yml`: materialisations per folder (staging/intermediate = `view`, marts = `table`), business rules as **vars** (`sla_minutes`, `local_timezone`, `response_outlier_days`, `late_record_hours`), `persist_docs` so descriptions reach the database.
- `dbt/profiles.yml` is committed: it contains **no secrets**, only `env_var('LF_DB_PATH', default)`. Run dbt from the repository root: `dbt build --project-dir dbt --profiles-dir dbt`.
- `generate_schema_name` macro override: schemas are named `staging`, `intermediate`, `marts`, `reference` instead of dbt's default `main_staging`, which is easier for analysts and BI tools.
- `packages.yml` + committed `package-lock.yml` (dbt_utils 1.4.1): the package version is reproducible, like a Python lock file.
- `_crm__sources.yml` declares the raw tables with **freshness** on `_loaded_at` (warn 24 h, error 72 h) — the *timeliness* dimension of data quality. `dbt source freshness` passes on freshly ingested data.
- **Deviation from step 6 (decision):** `.sqlfluff` keeps the `jinja` templater with dbt builtins instead of the `dbt` templater. The dbt templater needs dbt, installed packages and a working profile at lint time, both in pre-commit and in the CI lint job; the jinja one is fast and self-contained. Trade-off: macros from packages are not expanded during linting. Added `.sqlfluffignore` for dbt build artefacts.
