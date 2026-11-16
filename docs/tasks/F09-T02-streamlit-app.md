# F09-T02 — Build the Streamlit dashboard

| Field | Value |
|---|---|
| **Feature** | [F09 — KPI dashboard](../features/F09-dashboard.md) |
| **Status** | To Do |
| **Estimate** | 3 h |
| **Depends on** | F09-T01 |
| **Branch** | `feat/F09-T02-streamlit-app` |

## Description

Pages: Overview, Funnel, SLA & response time, Teams & agents.

## Steps

1. Read-only DuckDB connection to marts; cache queries (`st.cache_data`)
2. Filters: period, channel, source, team
3. KPI tiles with deltas vs previous period; funnel chart; response-time distribution; team table
4. Queries live in `dashboard/queries.py`, not inline in UI code

## Acceptance criteria

- [ ] `streamlit run src/lead_funnel/dashboard/app.py` works
- [ ] Numbers reconcile with `sql/analysis/01_funnel_kpis.sql`

## Deliverables

- `src/lead_funnel/dashboard/`
- screenshots in `reports/figures/`

## Why this matters (best practice)

Separating queries from UI is the same *separation of concerns* principle used in web development.

## Notes

_Add decisions, problems found and links to the PR here while working._
