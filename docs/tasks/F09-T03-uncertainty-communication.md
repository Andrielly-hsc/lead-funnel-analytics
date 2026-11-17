# F09-T03 — Communicate uncertainty in the dashboard

| Field | Value |
|---|---|
| **Feature** | [F09 — KPI dashboard](../features/F09-dashboard.md) |
| **Status** | Done |
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

- Part of the uncertainty work shipped with the app in F09-T02 (Wilson CI whiskers on every compared rate, n < 100 warnings for the whole selection, groups and agents, causal/synthetic-data caveat in the sidebar). This task adds the two places where dashboards mislead most:
- **Noise-aware KPI deltas:** each rate's change vs the previous period is tested (two-proportion z-test, 95 %, `queries.change_is_noise`). Changes within sampling noise are shown in **grey** with a tooltip saying so, instead of red/green. On the last four weeks of seed 42 all three rate deltas (−0.6, −0.6, −0.1 pp) are grey — exactly the kind of "drop" managers otherwise ask teams to explain. Approximation: the lead count is used as n for every rate.
- **"How to read the uncertainty"** section in the Definitions tab: whiskers, grey deltas, n < 100, association vs cause, synthetic data.
- Delta formatting fixed: `€-1,348,623` → `-€1.3 M`; sign first for every non-rate KPI.
- Tests: the noise rule on four cases (small change on large n, real change, large change on tiny n, no data) and an `AppTest` check that deltas, the grey-delta caption and the explanation render.
