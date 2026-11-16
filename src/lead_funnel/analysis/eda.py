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
