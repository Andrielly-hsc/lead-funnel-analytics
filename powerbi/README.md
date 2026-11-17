# Power BI version (optional, not built yet)

> **Status: deferred.** The assets below are ready, but the `.pbix` report has not been
> built: it requires Power BI Desktop (Windows) and its graphical interface. The DAX
> measures were written to mirror the SQL metric layer and **have not been validated in
> Power BI yet** — use the reconciliation table below before trusting them.

Why it is worth doing: iSYS works in the Microsoft ecosystem (Fabric, Power BI). Building the
same KPIs on the *same star schema* in a second tool demonstrates that the dimensional model
is tool-agnostic — the point of Kimball modelling.

## Steps

1. Build the warehouse: `lead-funnel generate && lead-funnel ingest && dbt build --project-dir dbt --profiles-dir dbt`.
2. Export the marts: `python scripts/export_bi.py` → `data/bi/*.parquet`.
3. Power BI Desktop → *Get data → Parquet* → import the seven files.
4. *Model view*: create the star schema relationships (single direction, many-to-one):

   | From (many) | To (one) |
   |---|---|
   | `fct_leads[created_date_key]` | `dim_date[date_key]` |
   | `fct_leads[channel_key]` | `dim_channel[channel_key]` |
   | `fct_leads[lead_source_key]` | `dim_lead_source[lead_source_key]` |
   | `fct_leads[campaign_key]` | `dim_campaign[campaign_key]` |
   | `fct_leads[owner_agent_key]` | `dim_agent[agent_key]` |
   | `fct_interactions[lead_key]` | `fct_leads[lead_key]` |
   | `fct_interactions[agent_key]` | `dim_agent[agent_key]` |
   | `fct_interactions[event_date_key]` | `dim_date[date_key]` (inactive if ambiguous) |

5. Mark `dim_date` as the date table (`date_day`).
6. Create the measures from [`measures.dax`](measures.dax).
7. **Reconcile** before building visuals — card visuals with no filters must show:

   | Measure | Expected (seed 42, 50 000 leads) |
   |---|---|
   | Leads | 50,000 |
   | Response rate | 95.77 % |
   | SLA met | 41.59 % |
   | Median minutes to first response | 77.2 |
   | P90 minutes to first response | 900.9 |
   | Conversion rate | 15.60 % |
   | Pipeline value | €228,691,745 |

   These are the numbers of `sql/analysis/01_funnel_kpis.sql` (Q1) and of the Streamlit
   dashboard; a difference means a measure or a relationship is wrong.
8. Save as `powerbi/lead_funnel.pbix` and add screenshots to `reports/figures/`.
