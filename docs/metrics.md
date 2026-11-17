# KPI definitions

> **Generated from `src/lead_funnel/dashboard/metrics.py` — do not edit by hand.**
> Regenerate with `python -m lead_funnel.dashboard.metrics > docs/metrics.md`.
> The dashboard computes every number from these exact expressions, and a test checks
> that the headline KPIs reconcile with `sql/analysis/01_funnel_kpis.sql`.

**Grain:** one row per lead, `marts.fct_leads` (alias `f`). **Base filter:** `not f.is_probable_duplicate`. Targets are illustrative business targets, not statistical ones.

| KPI | Business question | Formula (SQL) | Unit | Filters | Owner | Target |
|---|---|---|---|---|---|---|
| **Leads** | How many unique leads entered the CRM? | `count(*)` | count | probable duplicates excluded (KI-01) | Marketing | — |
| **Response rate** | What share of leads received at least one contact? | `avg(f.is_responded::int)` | rate | probable duplicates excluded | Head of Customer Support | ≥ 98 % |
| **SLA met** | What share of leads was answered within 60 minutes? | `avg(f.is_sla_met::int)` | rate | duplicates excluded; leads with an invalid response time drop out (is_sla_met is null for them) | Head of Customer Support | ≥ 50 % |
| **Median time to first response** | How long does a typical lead wait for the first contact? | `median(f.minutes_to_first_response) filter (where not f.is_response_time_invalid)` | minutes | answered leads with a valid response time | Head of Customer Support | ≤ 60 min |
| **p90 time to first response** | How long do the slowest 10 % of answered leads wait? | `quantile_cont(f.minutes_to_first_response, 0.9) filter (where not f.is_response_time_invalid)` | minutes | answered leads with a valid response time | Head of Customer Support | — |
| **Conversion rate** | What share of leads became an opportunity? | `avg(f.is_converted::int)` | rate | probable duplicates excluded | Sales | — |
| **Pipeline value** | What is the expected value of the opportunities created? | `coalesce(sum(f.opportunity_amount_eur), 0)` | eur | probable duplicates excluded | Sales | — |
| **Pipeline per lead** | How much pipeline does an average lead generate? | `coalesce(sum(f.opportunity_amount_eur), 0) / count(*)` | eur | probable duplicates excluded | Marketing | — |
| **Touches per lead** | How much agent effort does a lead receive? | `avg(f.n_touches)` | count | probable duplicates excluded; leads never contacted count as 0 | Head of Customer Support | — |

## Caveats

- **Leads:** Only leads registered in the CRM (limitation L1).
- **Response rate:** Including duplicates would understate it (duplicates are never contacted).
- **SLA met:** Structurally 0 % for leads created outside Mon-Fri 08:00-18:00 (L6). Never-answered leads count as missed.
- **Median time to first response:** Median, not mean: the distribution is extremely skewed (mean ≈ 6× median).
- **p90 time to first response:** Dominated by leads waiting overnight or over a weekend.
- **Conversion rate:** Differences between groups are associations, not effects: lead quality differs between groups (see reports/analysis_report.md).
- **Pipeline value:** Expected deal value at opportunity creation — pipeline, not revenue.
- **Pipeline per lead:** Use to compare sources and campaigns; sensitive to a few large deals.
- **Touches per lead:** Higher for good leads (agents work them harder) — a mediator, not a driver.
