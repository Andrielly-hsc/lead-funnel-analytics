# F04-T06 — Document models and publish lineage

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | Done |
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

- **100 % documentation:** every model has a description with its grain, and all 136 columns of the 14 models are documented (measured from `manifest.json` vs `catalog.json`).
- **Doc blocks** (`dbt/models/_docs.md`) hold shared definitions written once and referenced with `{{ doc() }}` — e.g. the SLA rule `is_sla_met` and `minutes_to_first_response` ("null, not zero"), used identically in intermediate and marts. One definition = no contradictory documentation.
- **Exposures** (`exposures.yml`): the KPI dashboard (F09) and the SLA analysis (F08) are declared as consumers, so the lineage answers "what breaks if I change this model?".
- **Lineage as code:** `scripts/dbt_lineage.py` renders `docs/lineage.md` (Mermaid, readable on GitHub) from `manifest.json`; `--check` runs in the CI e2e job and fails if the diagram is outdated. This replaced the planned screenshot: a screenshot cannot be reviewed in a diff and goes stale silently.
- `ARCHITECTURE.md` §5.2 updated to the model as built (lead_source, dim_campaign with `'-1'` member, point-in-time agent join, SCD2 from source history).
- Column descriptions were added with a one-off helper (not committed) that re-serialised the YAML files; their style is now uniform (block lists, folded long descriptions).
