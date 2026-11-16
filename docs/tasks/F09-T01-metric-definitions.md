# F09-T01 — Define the KPIs (metric layer document)

| Field | Value |
|---|---|
| **Feature** | [F09 — KPI dashboard](../features/F09-dashboard.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
