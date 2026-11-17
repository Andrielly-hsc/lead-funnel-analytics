# F09-T01 — Define the KPIs (metric layer document)

| Field | Value |
|---|---|
| **Feature** | [F09 — KPI dashboard](../features/F09-dashboard.md) |
| **Status** | Done |
| **Estimate** | 1 h |
| **Depends on** | — |
| **Branch** | `feat/F09-T01-metric-definitions` |

## Description

One agreed definition per metric.

## Steps

1. For each KPI: name, business question, formula (SQL), grain, filters, owner, target, caveats
2. KPIs: lead volume, conversion rate, median & p90 time to first response, SLA compliance, touches per lead, revenue per lead

## Acceptance criteria

- [ ] Every dashboard number maps to one definition

## Deliverables

- `docs/metrics.md`

## Why this matters (best practice)

Metric definitions are the contract between data team and business — the root of “why do two reports show different numbers?”

## Notes

- **Metric layer as code:** `dashboard/metrics.py` defines the 9 KPIs once — business question, SQL expression over `marts.fct_leads`, unit, filters, owner, illustrative target, caveat — and `kpi_select(where)` computes them all in one query. `docs/metrics.md` is **generated** from it and kept in sync by a test (same pattern as the data dictionary).
- KPIs: leads, response rate, SLA met, median and p90 time to first response, conversion rate, pipeline value, pipeline per lead, touches per lead. "Revenue per lead" from the original task was renamed **pipeline per lead**: the data has expected deal value at opportunity creation, not revenue — calling it revenue would overstate what is known.
- Caveats encode earlier findings: SLA structurally 0 % outside business hours (L6), median not mean (skew), group differences are associations not effects (F08), touches are a mediator.
- On the seed-42 warehouse the KPIs equal the F06 query results exactly (95.77 % response, 41.59 % SLA, 77.2 / 900.9 min, 15.60 % conversion, €228.7 M pipeline); the automated reconciliation test comes with the app (F09-T02).
- New dependency: `streamlit` (with `altair` for charts). `pip-compile` failed three times on the known SSL flakiness of the dbt parser download before succeeding on the fourth attempt.
