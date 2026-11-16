# F09-T04 — (Optional) Build a Power BI version

| Field | Value |
|---|---|
| **Feature** | [F09 — KPI dashboard](../features/F09-dashboard.md) |
| **Status** | To Do |
| **Estimate** | 3 h |
| **Depends on** | F09-T03 |
| **Branch** | `feat/F09-T04-power-bi-optional` |

## Description

Mirror the main page in Power BI, the tool used in many iSYS projects (Microsoft Fabric ecosystem).

## Steps

1. Export marts to Parquet
2. Power BI Desktop: import Parquet, model relationships as star schema, DAX measures matching `docs/metrics.md`
3. Save `.pbix` and screenshots

## Acceptance criteria

- [ ] DAX measures match Streamlit numbers

## Deliverables

- `powerbi/lead_funnel.pbix`
- screenshots

## Why this matters (best practice)

Shows that the same dimensional model serves any BI tool — the point of a well-designed star schema.

## Notes

_Add decisions, problems found and links to the PR here while working._
