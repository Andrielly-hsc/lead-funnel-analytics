# F09-T04 — (Optional) Build a Power BI version

| Field | Value |
|---|---|
| **Feature** | [F09 — KPI dashboard](../features/F09-dashboard.md) |
| **Status** | Deferred (optional) |
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

- **Status: Deferred.** Building the `.pbix` needs Power BI Desktop and its GUI, which could not be operated in this setup. Everything else is ready:
  - `scripts/export_bi.py` exports the seven marts to `data/bi/*.parquet` (types preserved: `DATE`, `INTEGER`, booleans — a CSV export would lose them);
  - `powerbi/measures.dax` mirrors the nine KPIs of the metric layer, with comments on the DAX ↔ SQL equivalences (blank handling in `MEDIAN`, `PERCENTILE.INC` = `quantile_cont`, the SLA denominator);
  - `powerbi/README.md` gives the import steps, the star-schema relationships and a **reconciliation table** of expected values.
- The DAX measures are **not validated** in Power BI; the reconciliation table is how to validate them. Not marked Done for that reason.
