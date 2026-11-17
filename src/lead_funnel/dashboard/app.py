"""Lead funnel KPI dashboard.

    streamlit run src/lead_funnel/dashboard/app.py

UI only: every number comes from ``dashboard/queries.py`` (which uses the metric layer in
``dashboard/metrics.py``). The warehouse is opened read-only.
"""

from __future__ import annotations

from datetime import date

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

from lead_funnel.analysis import viz
from lead_funnel.config import get_settings
from lead_funnel.dashboard import metrics, queries
from lead_funnel.dashboard.queries import Filters

TEAM_LABELS = {
    "inbound_dach": "Inbound DACH",
    "inbound_international": "Inbound international",
    "partner": "Partner",
    "enterprise": "Enterprise",
}
CAVEAT = (
    "Synthetic data (seed 42). Differences between groups are **associations**: lead "
    "quality differs between channels, sources and teams, so a higher rate is not proof "
    "that a group *causes* better results — see the analysis report."
)

st.set_page_config(page_title="Lead funnel KPIs", page_icon="📈", layout="wide")


# ----------------------------------------------------------------------------------
# data access (cached)
# ----------------------------------------------------------------------------------
@st.cache_resource
def connection() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(get_settings().db_path), read_only=True)
    con.execute("set TimeZone = 'UTC'")
    return con


@st.cache_data(show_spinner=False)
def cached(name: str, filters: Filters, *args) -> pd.DataFrame | pd.Series:
    return getattr(queries, name)(connection(), filters, *args)


def ink() -> str:
    """Text colour for chart annotations in the active theme. Altair's default text colour
    does not follow Streamlit's dark mode, which made the mandatory direct labels unreadable."""
    theme = getattr(st.context, "theme", None)
    return "#f0efec" if theme is not None and theme.type == "dark" else viz.TEXT_PRIMARY


def label(value: str) -> str:
    return TEAM_LABELS.get(value) or viz.label(value)


def fmt(value: float, unit: str) -> str:
    if pd.isna(value):
        return "–"
    if unit == "rate":
        return f"{value:.1%}"
    if unit == "minutes":
        return f"{value / 60:.1f} h" if value >= 120 else f"{value:.0f} min"
    if unit == "eur":
        return f"€{value / 1e6:.1f} M" if value >= 1e6 else f"€{value:,.0f}"
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:.2f}"


# ----------------------------------------------------------------------------------
# sidebar: filters
# ----------------------------------------------------------------------------------
con = connection()
first, last = queries.date_bounds(con)
with st.sidebar:
    st.header("Filters")
    period = st.date_input("Period", value=(first, last), min_value=first, max_value=last)
    start, end = period if isinstance(period, tuple) and len(period) == 2 else (first, last)
    channels = st.multiselect(
        "Channel", queries.options(con, "channel"), format_func=label, placeholder="All"
    )
    sources = st.multiselect(
        "Lead source", queries.options(con, "lead_source"), format_func=label, placeholder="All"
    )
    teams = st.multiselect(
        "Team", queries.options(con, "team"), format_func=label, placeholder="All"
    )
    st.caption(CAVEAT)

filters = Filters(start, end, tuple(channels), tuple(sources), tuple(teams))
st.title("Lead funnel KPIs")
st.caption(
    f"{start:%d %b %Y} – {end:%d %b %Y} · definitions: docs/metrics.md · "
    "probable duplicates excluded"
)

overview, funnel_tab, sla_tab, teams_tab, about = st.tabs(
    ["Overview", "Funnel", "SLA & response time", "Teams & agents", "Definitions"]
)

# ----------------------------------------------------------------------------------
# overview
# ----------------------------------------------------------------------------------
with overview:
    current = cached("kpis", filters)
    previous = cached("kpis", filters.previous_period())
    if current["leads"] == 0:
        st.warning("No leads match these filters.")
    else:
        if current["leads"] < queries.SMALL_N:
            st.warning(
                f"Only {int(current['leads'])} leads match these filters — rates below are "
                "too uncertain to compare (n < 100)."
            )
        has_previous = previous["leads"] > 0
        shown = [m for m in metrics.METRICS if m.key != "pipeline_per_lead_eur"]
        for row in (shown[:4], shown[4:]):
            for col, m in zip(st.columns(len(row)), row, strict=True):
                delta, colour, note = None, "normal", ""
                if has_previous and pd.notna(previous[m.key]):
                    diff = current[m.key] - previous[m.key]
                    if m.unit == "rate":
                        delta = f"{diff * 100:+.1f} pp"
                    else:  # sign first, then the formatted magnitude: "-€1.3 M", "+4 min"
                        delta = ("-" if diff < 0 else "+") + fmt(abs(diff), m.unit)
                    colour = "inverse" if m.unit == "minutes" else "normal"  # shorter is better
                    if m.unit == "rate" and queries.change_is_noise(
                        current[m.key], current["leads"], previous[m.key], previous["leads"]
                    ):
                        colour = "off"  # grey: not distinguishable from sampling noise
                        note = " The change vs the previous period is within sampling noise."
                col.metric(
                    m.name,
                    fmt(current[m.key], m.unit),
                    delta,
                    delta_color=colour,
                    help=f"{m.question} Formula: {m.sql}. {m.caveat}{note}",
                )
        st.caption(
            "Deltas compare with the previous period of the same length"
            + (
                "; grey deltas on rates are within sampling noise (two-proportion test, 95 %)."
                if has_previous
                else " (not available: the period starts with the data)."
            )
        )

        weeks = cached("weekly", filters)
        weeks = weeks[~weeks["is_partial"]]
        left, right = st.columns(2)
        base = alt.Chart(weeks).encode(x=alt.X("week_start:T", title=None))
        left.altair_chart(
            base.mark_line(color=viz.SERIES[0])
            .encode(y=alt.Y("leads:Q", title="Leads per week"))
            .properties(title="Leads per ISO week", height=260),
            width="stretch",
        )
        right.altair_chart(
            base.mark_line(color=viz.SERIES[0])
            .encode(
                y=alt.Y(
                    "sla_rate:Q",
                    title="SLA met",
                    axis=alt.Axis(format="%"),
                    scale=alt.Scale(domain=[0, 1]),
                )
            )
            .properties(title="SLA met per ISO week", height=260),
            width="stretch",
        )
        st.caption("Two charts instead of one dual-axis chart; partial weeks are left out.")

# ----------------------------------------------------------------------------------
# funnel
# ----------------------------------------------------------------------------------
with funnel_tab:
    f = cached("funnel", filters)
    st.altair_chart(
        alt.Chart(f)
        .mark_bar(color=viz.SERIES[0], cornerRadiusEnd=4)
        .encode(
            x=alt.X("leads:Q", title="Leads"),
            y=alt.Y("stage:N", sort=list(f["stage"]), title=None),
            tooltip=[
                "stage",
                alt.Tooltip("leads:Q", format=","),
                alt.Tooltip("cumulative_conversion:Q", format=".1%", title="of created"),
            ],
        )
        .properties(
            height=220,
            title="Nested funnel: each stage counts only leads that passed the previous ones",
        ),
        width="stretch",
    )
    st.dataframe(
        f,
        hide_index=True,
        column_config={
            "leads": st.column_config.NumberColumn(format="%d"),
            "step_conversion": st.column_config.NumberColumn("vs previous stage", format="percent"),
            "cumulative_conversion": st.column_config.NumberColumn("vs created", format="percent"),
        },
    )


# ----------------------------------------------------------------------------------
# SLA and response time
# ----------------------------------------------------------------------------------
def rate_chart(t: pd.DataFrame, rate: str, title: str, colors: dict | None) -> alt.Chart:
    """Horizontal bars with 95 % CI whiskers and direct labels; fixed colours per entity."""
    data = t.assign(label=t["grp"].map(label), lo=t[f"{rate}_lo"], hi=t[f"{rate}_hi"])
    data["text"] = data.apply(lambda r: f"{r[f'{rate}_rate']:.1%} (n={r['n']:,})", axis=1)
    order = list(data.sort_values(f"{rate}_rate", ascending=False)["label"])
    y = alt.Y("label:N", sort=order, title=None, axis=alt.Axis(labelLimit=220))
    if colors:
        color = alt.Color(
            "grp:N",
            scale=alt.Scale(domain=list(colors), range=list(colors.values())),
            legend=None,
        )
    else:
        color = alt.value(viz.SERIES[0])
    bars = (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X(
                f"{rate}_rate:Q",
                title=None,
                # room on the right for the direct labels, ticks only up to 100 %
                scale=alt.Scale(domain=[0, float(data["hi"].max()) * 1.7]),
                axis=alt.Axis(format="%", values=[i / 10 for i in range(11)]),
            ),
            y=y,
            color=color,
            tooltip=[
                "label",
                alt.Tooltip(f"{rate}_rate:Q", format=".1%"),
                alt.Tooltip("lo:Q", format=".1%"),
                alt.Tooltip("hi:Q", format=".1%"),
                alt.Tooltip("n:Q", format=","),
            ],
        )
    )
    # theme-aware colour: readable in light and dark mode
    whiskers = (
        alt.Chart(data).mark_rule(strokeWidth=1.5, color=ink()).encode(x="lo:Q", x2="hi:Q", y=y)
    )
    text = (
        alt.Chart(data)
        .mark_text(align="left", dx=6, color=ink())
        .encode(x="hi:Q", y=y, text="text:N")
    )
    return (bars + whiskers + text).properties(title=title, height=40 * len(data) + 40)


with sla_tab:
    left, right = st.columns(2)
    by_channel = cached("by_dimension", filters, "channel")
    by_source = cached("by_dimension", filters, "lead_source")
    left.altair_chart(
        rate_chart(by_channel, "sla", "SLA met by channel", viz.CHANNEL_COLORS),
        width="stretch",
    )
    right.altair_chart(
        rate_chart(by_source, "sla", "SLA met by lead source", viz.SOURCE_COLORS),
        width="stretch",
    )
    small = pd.concat([by_channel, by_source]).query("small_sample")
    if not small.empty:
        st.warning(
            "Small groups (n < 100): "
            + ", ".join(label(g) for g in small["grp"])
            + " — their rates and intervals are too wide to rank."
        )
    st.caption("Whiskers: 95 % Wilson confidence intervals.")

    grid = cached("weekday_hour", filters)
    days = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    grid = grid.assign(day=grid["iso_day_of_week"].map(days))
    st.altair_chart(
        alt.Chart(grid)
        .mark_rect()
        .encode(
            x=alt.X("local_hour:O", title="Local hour of creation"),
            y=alt.Y(
                "day:N", sort=list(days.values()), title=None, axis=alt.Axis(labelOverlap=False)
            ),
            color=alt.Color(
                "sla_rate:Q",
                title="SLA met",
                scale=alt.Scale(range=[viz.SEQUENTIAL[0], viz.SEQUENTIAL[-1]], domain=[0, 1]),
                legend=alt.Legend(format="%"),
            ),
            tooltip=[
                "day",
                "local_hour",
                alt.Tooltip("sla_rate:Q", format=".0%"),
                alt.Tooltip("leads:Q", format=","),
            ],
        )
        .properties(
            height=280, title="SLA met by weekday × local hour — 0 % outside Mon-Fri 08:00-18:00"
        ),
        width="stretch",
    )

# ----------------------------------------------------------------------------------
# teams and agents
# ----------------------------------------------------------------------------------
with teams_tab:
    by_team = cached("by_dimension", filters, "team")
    st.altair_chart(rate_chart(by_team, "sla", "SLA met by team", None), width="stretch")
    agent_table = cached("agents", filters).assign(team=lambda t: t["team"].map(label))
    n_small = int(agent_table["small_sample"].sum())
    if n_small:
        st.warning(
            f"{n_small} of {len(agent_table)} agents handled fewer than 100 leads in this "
            "selection: do not rank them — the intervals overlap."
        )
    st.dataframe(
        agent_table[
            [
                "agent_id",
                "team",
                "n",
                "sla_rate",
                "sla_lo",
                "sla_hi",
                "conversion_rate",
                "median_response_min",
                "small_sample",
            ]
        ],
        hide_index=True,
        column_config={
            "n": st.column_config.NumberColumn("leads", format="%d"),
            "sla_rate": st.column_config.NumberColumn("SLA met", format="percent"),
            "sla_lo": st.column_config.NumberColumn("CI low", format="percent"),
            "sla_hi": st.column_config.NumberColumn("CI high", format="percent"),
            "conversion_rate": st.column_config.NumberColumn("conversion", format="percent"),
            "median_response_min": st.column_config.NumberColumn(
                "median response (min)", format="%.0f"
            ),
            "small_sample": st.column_config.CheckboxColumn("n < 100"),
        },
    )
    st.info(
        "Agent-level KPIs describe workload and context (team, channel mix, lead quality), "
        "not individual performance. Using them to rate people would be a use outside their "
        "purpose."
    )

# ----------------------------------------------------------------------------------
# definitions
# ----------------------------------------------------------------------------------
with about:
    st.markdown(
        """
### How to read the uncertainty

- **Whiskers** on rates are 95 % confidence intervals (Wilson): the range of rates that
  are compatible with the data. If two groups' intervals overlap a lot, do not rank them.
- **Grey deltas** on the KPI tiles mean the change since the previous period is within
  what random variation alone would produce — no action is needed to "explain" it.
- **n < 100**: rates on fewer than 100 leads move by several points from week to week by
  chance alone; the dashboard warns instead of letting them be compared.
- **Association, not cause.** Channels, sources and teams receive leads of different
  quality, so a higher rate does not show that the group itself *causes* better results.
  The causal analysis (adjusted for lead quality) is in `reports/analysis_report.md`.
- **Synthetic data:** every number here comes from a simulated CRM (seed 42).
"""
    )
    st.markdown(metrics.render_metrics_doc().split("\n", 2)[2])
    st.caption(f"Data refreshed from the warehouse · rendered {date.today():%d %b %Y}")
