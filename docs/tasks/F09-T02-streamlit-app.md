# F09-T02 — Build the Streamlit dashboard

| Field | Value |
|---|---|
| **Feature** | [F09 — KPI dashboard](../features/F09-dashboard.md) |
| **Status** | Done |
| **Estimate** | 3 h |
| **Depends on** | F09-T01 |
| **Branch** | `feat/F09-T02-streamlit-app` |

## Description

Pages: Overview, Funnel, SLA & response time, Teams & agents.

## Steps

1. Read-only DuckDB connection to marts; cache queries (`st.cache_data`)
2. Filters: period, channel, source, team
3. KPI tiles with deltas vs previous period; funnel chart; response-time distribution; team table
4. Queries live in `dashboard/queries.py`, not inline in UI code

## Acceptance criteria

- [ ] `streamlit run src/lead_funnel/dashboard/app.py` works
- [ ] Numbers reconcile with `sql/analysis/01_funnel_kpis.sql`

## Deliverables

- `src/lead_funnel/dashboard/`
- screenshots in `reports/figures/`

## Why this matters (best practice)

Separating queries from UI is the same *separation of concerns* principle used in web development.

## Notes

- `dashboard/queries.py`: `Filters` (period, channels, sources, teams; always **bound parameters**, `list_contains(?::varchar[], …)`), `previous_period()` for KPI deltas, `kpis()` (reuses the metric layer), nested `funnel()`, `by_dimension()` and `agents()` with 95 % Wilson CIs and a `small_sample` flag (n < 100), `weekly()` with partial weeks flagged, `weekday_hour()`, `reconcile_with_sql()`.
- `dashboard/app.py` (UI only): sidebar filters; tabs Overview (8 KPI tiles with deltas and tooltips holding each metric's formula and caveat, weekly volume and SLA as two charts — never a dual axis), Funnel, SLA & response time (bars with CI whiskers and direct labels in the fixed entity colours, weekday × hour heatmap), Teams & agents (table with CIs and n < 100 flag, plus a note that agent KPIs are not individual performance ratings), Definitions (rendered from the metric layer). Cached read-only connection and cached queries.
- **F06 deferred criterion closed:** the dashboard's KPIs equal Q1 of `sql/analysis/01_funnel_kpis.sql` on all 7 headline numbers — two independent implementations of the same definitions. Checked by an integration test and in CI by `scripts/check_dashboard.py` (reconciliation + Streamlit `AppTest` smoke test on the e2e warehouse).
- **Found while looking at the real app (dark theme):** the mandatory direct labels and CI whiskers were drawn in the light-theme text colour and were nearly invisible; Altair's default text colour does not follow Streamlit's dark mode, so the colour is now chosen from `st.context.theme`. Also fixed: weekday labels hidden by overlap on the heatmap, labels clipped at the right edge, truncated "Inbound international". And one self-inflicted bug: a `sed` edit put `.encode(...)` inside a comment — valid Python, so lint passed; caught by re-reading the code before reloading.
- `date_bounds()` initially ignored the base filter, so the default period ended on 4 Jan 2026 — dates that only contain duplicates. Fixed.
- Deprecation fixed before it breaks: `use_container_width` → `width="stretch"` (removal announced by Streamlit).
- My own test mistake: I asserted an agent small-sample warning on the full period, but the test warehouse has ~200 leads per agent; the warning correctly appears only for a one-day selection.
