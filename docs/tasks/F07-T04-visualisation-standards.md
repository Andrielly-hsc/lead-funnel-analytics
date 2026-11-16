# F07-T04 — Implement figure standards

| Field | Value |
|---|---|
| **Feature** | [F07 — Exploratory & descriptive analysis](../features/F07-exploratory-analysis.md) |
| **Status** | Done |
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

- Done **first** in F07 (order changed): every EDA figure depends on these helpers.
- `analysis/viz.py` now encodes the project's chart rules: fixed colour per entity (`CHANNEL_COLORS`, `SOURCE_COLORS` — colour follows the entity, never its rank), categorical slots in fixed order, one-hue `SEQUENTIAL` ramp for magnitudes, reserved status colours, display `label()`s, `percent_axis()`, `bars_with_ci()` (CI whiskers + mandatory direct labels "value (n=…)"), `caption()` and `save_fig()`.
- The six categorical colours were checked with the palette validator: all checks pass, with a contrast WARN (3 hues below 3:1 on the light surface) that *obliges* direct labels or a table view — `bars_with_ci` always draws them.
- Tests: every category has a distinct fixed colour and label, status colours are not reused as series colours, the sequential ramp darkens monotonically, labels render as expected.
- Dev dependencies for the thin EDA notebook: `ipykernel`, `nbclient`, `nbformat`.
- **Root cause of the "transient" `pip-compile` failures (F04-F05):** `dbt-core` 1.12 depends on `dbt-core-experimental-parser`, an sdist that downloads a binary from GitHub while building; that download intermittently fails SSL certificate verification in this environment. It is network flakiness, not a dependency conflict — retrying works. Also pinned `dbt-core>=1.9,<2` explicitly so the resolver can never pick dbt 2.x, matching `require-dbt-version` in `dbt_project.yml`.
