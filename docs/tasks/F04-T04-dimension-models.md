# F04-T04 — Build dimension models (incl. SCD Type 2)

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | Done |
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

- Five dimensions in `marts` (materialised as tables): `dim_date`, `dim_agent`, `dim_channel`, `dim_lead_source`, `dim_campaign`.
- **Surrogate keys** with `dbt_utils.generate_surrogate_key` (MD5 of the natural key). `dim_date` uses the conventional integer smart key `YYYYMMDD`.
- **`dim_agent` is SCD type 2** built directly from the history in the HR export (`valid_from` inclusive, `valid_to` exclusive) — no dbt snapshot needed, because the source does not overwrite history (decision recorded in F02-T01). A singular test (`assert_dim_agent_versions_do_not_overlap`) guarantees versions are contiguous and never overlap.
- **"No campaign" member** (`campaign_key = '-1'`) in `dim_campaign`: fact foreign keys are never null, and BI tools show a label instead of a blank (Kimball practice).
- `dim_date` 2024-2026 with ISO calendar attributes and a `sequential_values` test (no missing days). Edge case worth knowing: 2025-12-29 belongs to **ISO week 1 of ISO year 2026**, so weekly reports must group by `iso_year` + `iso_week`, never `year` + `iso_week`.
- `dim_lead_source` adds business attributes (`is_paid_media`, `has_campaigns`); `dim_channel` adds display labels.
- `dbt build --select marts`: 28 tests pass.
- Linting package macros: the jinja templater does not know `dbt_utils`. Added **Python stubs** in `dbt/lint_stubs/dbt_utils.py` (sqlfluff `library_path`) that return equivalent SQL for `generate_surrogate_key` and `date_spine`, so the models can be parsed. They are never used by dbt.
- Renamed reserved-word columns flagged by RF04: `year`/`quarter`/`month` → `calendar_year`/`calendar_quarter`/`month_of_year`.
