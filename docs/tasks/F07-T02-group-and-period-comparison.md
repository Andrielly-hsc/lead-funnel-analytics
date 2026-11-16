# F07-T02 — Compare groups and periods

| Field | Value |
|---|---|
| **Feature** | [F07 — Exploratory & descriptive analysis](../features/F07-exploratory-analysis.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F07-T01 |
| **Branch** | `feat/F07-T02-group-and-period-comparison` |

## Description

Find where performance differs.

## Steps

1. Conversion and response time by channel, source, team, company size
2. Weekly trend, weekday × hour heatmap
3. Before/after a team change (using SCD2)
4. Small multiples instead of overloaded charts

## Acceptance criteria

- [ ] Each comparison states n per group

## Deliverables

- Figures in `reports/figures/eda_*`

## Why this matters (best practice)

Always show group sizes: a 40 % conversion rate on 10 leads means little.

## Notes

- `eda.py` additions: `wilson_ci()`, `compare_groups()` (n, conversion and SLA rates with 95 % Wilson CIs, median response time), `plot_group_comparison()`, `weekly_trend()` with partial-week flag, `weekday_hour()` (7 × 24 matrix), `plot_periods()`, `team_change_comparison()` (SCD2, same agent before/after a team change). `agent_id` added to `load_leads()`.
- **Wilson, not Wald:** the textbook `p ± z·√(p(1−p)/n)` interval can leave [0, 1] and is too narrow for small n or extreme rates (0 successes in 10 gives [0, 0]); Wilson stays informative. Group sizes are always printed next to rates.
- **SLA denominator:** leads with an invalid response time have `is_sla_met = null` and are excluded from SLA denominators (`sla_n`), not counted as misses.
- Findings: phone leads meet the SLA 71 % of the time vs e-mail 18 %; partner leads convert at ~34 % vs social ~7 %; SLA rate is flat around 40-45 % all year while volume peaks in June-August; the weekday × hour heatmap shows SLA = 0 outside Mon-Fri 08:00-18:00; agents who changed team show no large SLA change before/after (descriptive only).
- **Two visual traps fixed:** (1) the first and last ISO weeks contain only 5 and 3 days of data and looked like a volume collapse — partial weeks are now flagged and left out, with a caption saying so (note: 29-31 Dec 2025 belong to ISO week 1 of 2026); (2) volume and SLA are two panels, never a dual axis.
- **Bug caught by a test:** `weekday_hour` filled missing cells *before* reindexing to the full 7 × 24 grid, so weekday-hours without any lead were NaN instead of 0. For volume an empty cell is 0; for the SLA rate it stays NaN (unknown, not 0 %).
