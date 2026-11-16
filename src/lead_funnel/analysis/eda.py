"""Exploratory and descriptive analysis of the lead funnel (F07).

All logic lives here (tested); ``notebooks/01_eda.ipynb`` only calls these functions
and shows their output. Every function takes a DataFrame and returns a new one or a
figure path — no hidden state, no printing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from lead_funnel.analysis import viz

# ----------------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------------
LEADS_SQL = """
select
    f.lead_id,
    f.created_at_local,
    hour(f.created_at_local) as local_hour,
    d.iso_year,
    d.iso_week,
    d.iso_day_of_week,
    c.channel,
    s.lead_source,
    a.agent_id,
    a.team,
    a.seniority,
    f.country_code,
    f.industry,
    f.company_size,
    f.company_size_band,
    f.lead_score,
    f.is_responded,
    f.minutes_to_first_response,
    f.is_sla_met,
    f.is_response_time_invalid,
    f.is_response_time_outlier,
    f.n_touches,
    f.n_meetings,
    f.is_converted,
    f.opportunity_amount_eur,
    f.days_to_opportunity,
    f.is_probable_duplicate
from marts.fct_leads as f
inner join marts.dim_date as d on f.created_date_key = d.date_key
inner join marts.dim_channel as c on f.channel_key = c.channel_key
inner join marts.dim_lead_source as s on f.lead_source_key = s.lead_source_key
inner join marts.dim_agent as a on f.owner_agent_key = a.agent_key
"""


def load_leads(con: duckdb.DuckDBPyConnection, *, include_duplicates: bool = False) -> pd.DataFrame:
    """One row per lead from the marts, with dimension attributes resolved.

    Probable duplicates are excluded by default (known issue KI-01): they are never
    contacted and would distort every response metric.
    """
    df = con.execute(LEADS_SQL).df()
    if not include_duplicates:
        df = df[~df["is_probable_duplicate"]].reset_index(drop=True)
    return df


# ----------------------------------------------------------------------------------
# Variable typing
# ----------------------------------------------------------------------------------
@dataclass(frozen=True)
class Variable:
    level: str  # identifier | nominal | ordinal | binary | discrete | continuous | datetime
    role: str  # id | dimension | measure | flag | time
    description: str


VARIABLES: dict[str, Variable] = {
    "lead_id": Variable("identifier", "id", "CRM key; no analytical meaning"),
    "created_at_local": Variable("datetime", "time", "creation time, local"),
    "local_hour": Variable("discrete", "time", "hour of creation 0-23 (cyclic)"),
    "iso_year": Variable("discrete", "time", "ISO week-numbering year"),
    "iso_week": Variable("discrete", "time", "ISO week 1-53"),
    "iso_day_of_week": Variable("ordinal", "time", "1 = Monday … 7 = Sunday"),
    "channel": Variable("nominal", "dimension", "how the lead arrived"),
    "lead_source": Variable("nominal", "dimension", "marketing source"),
    "agent_id": Variable("nominal", "dimension", "owning agent"),
    "team": Variable("nominal", "dimension", "owner's team at creation"),
    "seniority": Variable("ordinal", "dimension", "junior < mid < senior"),
    "country_code": Variable("nominal", "dimension", "ISO country"),
    "industry": Variable("nominal", "dimension", "industry (8 % missing, MCAR)"),
    "company_size": Variable("discrete", "measure", "employees (count; skewed)"),
    "company_size_band": Variable("ordinal", "dimension", "small < medium < large < enterprise"),
    "lead_score": Variable("discrete", "measure", "marketing score 0-100 (treated as interval)"),
    "is_responded": Variable("binary", "flag", "received at least one contact"),
    "minutes_to_first_response": Variable("continuous", "measure", "time to first contact"),
    "is_sla_met": Variable("binary", "flag", "answered within 60 min (null = invalid time)"),
    "is_response_time_invalid": Variable("binary", "flag", "clock-skew error"),
    "is_response_time_outlier": Variable("binary", "flag", "> 30 days, likely data error"),
    "n_touches": Variable("discrete", "measure", "number of interactions (count)"),
    "n_meetings": Variable("discrete", "measure", "number of meetings (count)"),
    "is_converted": Variable("binary", "flag", "became an opportunity (outcome)"),
    "opportunity_amount_eur": Variable("continuous", "measure", "deal value (converted only)"),
    "days_to_opportunity": Variable("continuous", "measure", "speed of conversion"),
    "is_probable_duplicate": Variable("binary", "flag", "near-duplicate (excluded)"),
}

ORDINAL_ORDER = {
    "seniority": ["junior", "mid", "senior"],
    "company_size_band": ["small", "medium", "large", "enterprise", "unknown"],
}


def variable_catalog(df: pd.DataFrame) -> pd.DataFrame:
    """Measurement level, role, dtype, missing share and distinct count of every column."""
    rows = []
    for col in df.columns:
        v = VARIABLES[col]
        rows.append(
            {
                "variable": col,
                "level": v.level,
                "role": v.role,
                "dtype": str(df[col].dtype),
                "pct_missing": round(100 * df[col].isna().mean(), 2),
                "distinct": int(df[col].nunique()),
                "description": v.description,
            }
        )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------
# Univariate description
# ----------------------------------------------------------------------------------
def frequency_table(series: pd.Series, order: list[str] | None = None) -> pd.DataFrame:
    """Absolute, relative and cumulative frequencies. Missing values get their own row.

    For ordinal variables pass ``order`` so the cumulative column is meaningful; nominal
    variables are sorted by frequency (their cumulative share is then a Pareto curve).
    """
    counts = series.fillna("(missing)").value_counts()
    if order is not None:
        counts = counts.reindex(
            [o for o in order if o in counts.index]
            + (["(missing)"] if "(missing)" in counts.index else [])
        )
    table = pd.DataFrame({"n": counts})
    table["pct"] = table["n"] / table["n"].sum()
    table["cum_pct"] = table["pct"].cumsum()
    table.index.name = series.name
    return table


def describe_numeric(series: pd.Series) -> pd.Series:
    """Position, dispersion and shape. Robust statistics (median, IQR, MAD) next to the
    classical ones, because skewed variables make the mean and std misleading."""
    s = series.dropna().astype(float)
    q = s.quantile([0.05, 0.25, 0.5, 0.75, 0.9, 0.95])
    return pd.Series(
        {
            "n": len(s),
            "missing": int(series.isna().sum()),
            "mean": s.mean(),
            "median": q[0.5],
            "mode": s.mode().iloc[0] if not s.empty else np.nan,
            "std": s.std(),
            "iqr": q[0.75] - q[0.25],
            "mad": (s - q[0.5]).abs().median(),
            "min": s.min(),
            "p05": q[0.05],
            "p25": q[0.25],
            "p75": q[0.75],
            "p90": q[0.9],
            "p95": q[0.95],
            "max": s.max(),
            "skewness": s.skew(),
            "excess_kurtosis": s.kurt(),
        },
        name=series.name,
    )


def valid_response_minutes(df: pd.DataFrame) -> pd.Series:
    """Response times usable for statistics: answered leads with a valid (non-negative)
    time. Outliers are kept here; F07-T03 decides how to treat them."""
    ok = df["is_responded"] & ~df["is_response_time_invalid"]
    return df.loc[ok, "minutes_to_first_response"]


def plot_distributions(df: pd.DataFrame, path: Path) -> Path:
    """Response time (log scale, right-skewed) next to lead score (roughly symmetric)."""
    viz.apply_style()
    hours = valid_response_minutes(df) / 60
    score = df["lead_score"]
    fig, (ax1, ax2) = viz.plt.subplots(1, 2, figsize=(11, 4))

    bins = np.logspace(np.log10(max(hours.min(), 1 / 60)), np.log10(hours.max()), 60)
    ax1.hist(hours.clip(lower=1 / 60), bins=bins, color=viz.SEQUENTIAL[7], zorder=2)
    ax1.set_xscale("log")
    med, p90, mean = hours.median(), hours.quantile(0.9), hours.mean()
    # labels at staggered heights so neighbouring reference lines never collide
    for (value, name), height in zip(
        ((med, "median"), (mean, "mean"), (p90, "p90")), (0.95, 0.80, 0.65), strict=True
    ):
        ax1.axvline(value, color=viz.TEXT_PRIMARY, linewidth=1, linestyle="--")
        ax1.text(value * 1.08, ax1.get_ylim()[1] * height, f"{name} {value:.1f} h", fontsize=8,
                 backgroundcolor=viz.SURFACE)  # fmt: skip
    ax1.set_xlabel("Hours to first response (log scale)")
    ax1.set_ylabel("Leads")
    ax1.set_title(f"Response time: right-skewed (skewness {hours.skew():.1f})")

    ax2.hist(score, bins=range(0, 102, 2), color=viz.SEQUENTIAL[7], zorder=2)
    ax2.axvline(score.mean(), color=viz.TEXT_PRIMARY, linewidth=1, linestyle="--")
    ax2.text(score.mean() + 1.5, ax2.get_ylim()[1] * 0.92, f"mean {score.mean():.1f}\n"
             f"median {score.median():.0f}", fontsize=8)  # fmt: skip
    ax2.set_xlabel("Lead score (0-100)")
    ax2.set_ylabel("Leads")
    skew = 0.0 if abs(score.skew()) < 0.005 else score.skew()  # avoid "-0.00"
    ax2.set_title(f"Lead score: roughly symmetric (skewness {skew:.2f})")
    fig.suptitle(
        f"The mean response time ({mean:.1f} h) is {mean / med:.0f}× the median "
        f"({med:.1f} h): report median and p90, not the mean",
        x=0.01, ha="left", fontweight="bold", fontsize=12,
    )  # fmt: skip
    fig.tight_layout()
    viz.caption(fig, f"n = {len(hours):,} answered leads with a valid response time; "
                "probable duplicates excluded.")  # fmt: skip
    return viz.save_fig(fig, path)


# ----------------------------------------------------------------------------------
# Group and period comparisons
# ----------------------------------------------------------------------------------
def wilson_ci(successes: np.ndarray | float, n: np.ndarray | float, z: float = 1.96):
    """Wilson score interval for a proportion.

    Preferred over the textbook ``p ± z·sqrt(p(1-p)/n)`` (Wald) interval, which can fall
    outside [0, 1] and is too narrow for small n or rates near 0 or 1.
    """
    successes, n = np.asarray(successes, dtype=float), np.asarray(n, dtype=float)
    p = np.divide(successes, n, out=np.zeros_like(n), where=n > 0)
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def compare_groups(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Per group: size, conversion and SLA rates with 95 % Wilson CIs, median response time."""
    g = df.groupby(by, observed=True)
    out = pd.DataFrame(
        {
            "n": g.size(),
            "conversions": g["is_converted"].sum(),
            "sla_n": g["is_sla_met"].count(),  # leads with a valid SLA flag
            "sla_met": g["is_sla_met"].sum(),
            "median_response_h": g["minutes_to_first_response"].median() / 60,
        }
    )
    out["conversion_rate"] = out["conversions"] / out["n"]
    out["conversion_lo"], out["conversion_hi"] = wilson_ci(out["conversions"], out["n"])
    out["sla_rate"] = out["sla_met"] / out["sla_n"]
    out["sla_lo"], out["sla_hi"] = wilson_ci(out["sla_met"], out["sla_n"])
    return out.sort_values("n", ascending=False)


def plot_group_comparison(df: pd.DataFrame, path: Path) -> Path:
    """Conversion and SLA rates by channel and by source, with CIs and group sizes."""
    viz.apply_style()
    fig, axes = viz.plt.subplots(2, 2, figsize=(12, 7.5))
    panels = [
        ("channel", "conversion", viz.CHANNEL_COLORS, axes[0, 0]),
        ("channel", "sla", viz.CHANNEL_COLORS, axes[1, 0]),
        ("lead_source", "conversion", viz.SOURCE_COLORS, axes[0, 1]),
        ("lead_source", "sla", viz.SOURCE_COLORS, axes[1, 1]),
    ]
    for by, metric, colors, ax in panels:
        t = compare_groups(df, by).sort_values(f"{metric}_rate", ascending=False)
        viz.bars_with_ci(
            ax,
            [viz.label(i) for i in t.index],
            t[f"{metric}_rate"],
            t[f"{metric}_lo"],
            t[f"{metric}_hi"],
            t["n"] if metric == "conversion" else t["sla_n"],
            [colors[i] for i in t.index],
        )
        viz.percent_axis(ax, "x")
        name = "Conversion rate" if metric == "conversion" else "SLA met (≤ 60 min)"
        ax.set_title(f"{name} by {by.replace('_', ' ')}")
    sla = compare_groups(df, "channel")["sla_rate"]
    fig.suptitle(
        f"Phone leads meet the SLA {sla['phone']:.0%} of the time, e-mail leads "
        f"{sla['email']:.0%}; partner leads convert best",
        x=0.01,
        ha="left",
        fontweight="bold",
        fontsize=12,
    )
    fig.tight_layout()
    viz.caption(
        fig,
        "Whiskers: 95 % Wilson confidence intervals. Probable duplicates excluded; "
        "SLA rates exclude invalid response times.",
    )
    return viz.save_fig(fig, path)


def weekly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Leads, conversion and SLA rate per ISO week (grouped by ISO year + ISO week).

    ``is_partial`` marks weeks with fewer than 7 observed days (the first and last week
    of the data): their volume is not comparable and would look like a collapse.
    """
    g = df.groupby(["iso_year", "iso_week"])
    out = pd.DataFrame(
        {
            "leads": g.size(),
            "days_observed": g["created_at_local"].agg(lambda s: s.dt.date.nunique()),
            "conversion_rate": g["is_converted"].mean(),
            "sla_rate": g["is_sla_met"].mean(),
        }
    ).reset_index()
    out["is_partial"] = out["days_observed"] < 7
    out["week_start"] = pd.to_datetime(
        out["iso_year"].astype(str) + "-W" + out["iso_week"].astype(str).str.zfill(2) + "-1",
        format="%G-W%V-%u",
    )
    return out


def weekday_hour(df: pd.DataFrame, value: str = "leads") -> pd.DataFrame:
    """7 × 24 matrix (ISO weekday × local hour) of lead counts or SLA rate."""
    if value == "leads":
        m = df.pivot_table(
            index="iso_day_of_week", columns="local_hour", values="lead_id", aggfunc="count"
        )
        # reindex first, then fill: an empty weekday-hour cell has 0 leads
        return m.reindex(index=range(1, 8), columns=range(24)).fillna(0)
    m = df.pivot_table(
        index="iso_day_of_week", columns="local_hour", values="is_sla_met", aggfunc="mean"
    )
    # an empty cell has an *unknown* SLA rate, not 0 %: keep NaN
    return m.reindex(index=range(1, 8), columns=range(24))


def plot_periods(df: pd.DataFrame, path: Path) -> Path:
    """Weekly volume and SLA (two panels, never a dual axis) + weekday × hour heatmaps."""
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.ticker import FuncFormatter

    viz.apply_style()
    fig = viz.plt.figure(figsize=(12, 8))
    grid = fig.add_gridspec(2, 2, height_ratios=[1, 1.15])
    all_weeks = weekly_trend(df)
    weekly = all_weeks[~all_weeks["is_partial"]]
    ax_vol = fig.add_subplot(grid[0, 0])
    ax_vol.plot(weekly["week_start"], weekly["leads"], color=viz.SERIES[0])
    ax_vol.set_title("Leads per ISO week")
    ax_vol.set_ylabel("Leads")
    ax_sla = fig.add_subplot(grid[0, 1], sharex=ax_vol)
    ax_sla.plot(weekly["week_start"], weekly["sla_rate"], color=viz.SERIES[0])
    viz.percent_axis(ax_sla)
    ax_sla.set_ylim(0, max(0.6, weekly["sla_rate"].max() * 1.1))
    ax_sla.set_title("SLA met per ISO week")

    cmap = LinearSegmentedColormap.from_list("sequential", viz.SEQUENTIAL)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    panels = (
        ("leads", "Leads by weekday × local hour"),
        ("sla", "SLA met by weekday × local hour"),
    )
    for col, (value, title) in enumerate(panels):
        ax = fig.add_subplot(grid[1, col])
        m = weekday_hour(df, value)
        im = ax.imshow(m.to_numpy(dtype=float), aspect="auto", cmap=cmap, vmin=0)
        ax.set_yticks(range(7), days)
        ax.set_xticks(range(0, 24, 2), [f"{h:02d}" for h in range(0, 24, 2)])
        ax.set_xlabel("Local hour of creation")
        ax.grid(False)
        ax.set_title(title)
        for spine in ax.spines.values():
            spine.set_visible(False)
        cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
        if value == "sla":
            cbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
    fig.suptitle(
        "Leads arrive in office hours, but those created after 18:00 or at weekends "
        "can never meet a 60-minute SLA",
        x=0.01,
        ha="left",
        fontweight="bold",
        fontsize=12,
    )
    fig.tight_layout()
    viz.caption(
        fig,
        f"Local time (Europe/Berlin). Probable duplicates excluded. "
        f"{int(all_weeks['is_partial'].sum())} partial weeks (fewer than 7 days of data) "
        "are left out of the weekly lines.",
    )
    return viz.save_fig(fig, path)


def team_change_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """SLA rate of agents who changed team, before vs after the change.

    Uses the point-in-time team stored on each lead (SCD type 2): the same agent appears
    under the old team for leads created before the change and under the new one after.
    """
    movers = df.groupby("agent_id")["team"].nunique()
    sub = df[df["agent_id"].isin(movers[movers > 1].index)]
    started = sub.groupby(["agent_id", "team"])["created_at_local"].min()
    period = started.groupby(level=0).rank().map({1.0: "before", 2.0: "after"}).rename("period")
    t = (
        sub.groupby(["agent_id", "team"])
        .agg(leads=("lead_id", "count"), sla_rate=("is_sla_met", "mean"))
        .join(period)
        .reset_index()
    )
    return t.sort_values(["agent_id", "period"], ascending=[True, False]).reset_index(drop=True)
