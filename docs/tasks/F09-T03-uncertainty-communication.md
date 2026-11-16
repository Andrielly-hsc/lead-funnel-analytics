# F09-T03 — Communicate uncertainty in the dashboard

| Field | Value |
|---|---|
| **Feature** | [F09 — KPI dashboard](../features/F09-dashboard.md) |
| **Status** | To Do |
| **Estimate** | 1 h |
| **Depends on** | F09-T02 |
| **Branch** | `feat/F09-T03-uncertainty-communication` |

## Description

Avoid misleading precision.

## Steps

1. Wilson CIs on conversion rates
2. Grey-out / warn segments with n < 100
3. Footnote: synthetic data, causal caveats

## Acceptance criteria

- [ ] Small-n warning visible when filtering to a tiny segment

## Deliverables

- dashboard components

## Why this matters (best practice)

Dashboards drive decisions; showing uncertainty prevents managers from rewarding or punishing teams for random noise.

## Notes

_Add decisions, problems found and links to the PR here while working._
