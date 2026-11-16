# F07-T04 — Implement figure standards

| Field | Value |
|---|---|
| **Feature** | [F07 — Exploratory & descriptive analysis](../features/F07-exploratory-analysis.md) |
| **Status** | To Do |
| **Estimate** | 1 h |
| **Depends on** | F07-T03 |
| **Branch** | `feat/F07-T04-visualisation-standards` |

## Description

Consistent, accessible, code-generated charts.

## Steps

1. `analysis/viz.py`: shared style (font size, colour-blind palette, fixed category colours), `save_fig(name)`
2. Insight-titled charts, units on axes, CI bands where relevant

## Acceptance criteria

- [ ] All report figures produced through `save_fig`

## Deliverables

- `src/lead_funnel/analysis/viz.py`

## Why this matters (best practice)

A shared plotting module gives a consistent visual identity — like a company design system for charts.

## Notes

_Add decisions, problems found and links to the PR here while working._
