"""Read-only queries behind the dashboard. No Streamlit here: plain functions of a DuckDB
connection and a :class:`Filters` value, so they are testable and reusable.

Filters are always passed as bound parameters (``?``), never concatenated into SQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import duckdb
import numpy as np
import pandas as pd

from lead_funnel.dashboard import metrics

SMALL_N = 100  # groups smaller than this get a warning instead of a confident rate

# one row per lead with the dimension attributes the dashboard filters and groups by
LEADS_RELATION = """(
    select
        f.*,
        c.channel,
        c.channel_label,
        s.lead_source,
        s.lead_source_label,
        a.agent_id,
        a.team,
        d.date_day,
        d.iso_year,
        d.iso_week,
        d.iso_day_of_week
    from marts.fct_leads as f
    inner join marts.dim_channel as c on f.channel_key = c.channel_key
    inner join marts.dim_lead_source as s on f.lead_source_key = s.lead_source_key
    inner join marts.dim_agent as a on f.owner_agent_key = a.agent_key
    inner join marts.dim_date as d on f.created_date_key = d.date_key
)"""


@dataclass(frozen=True)
class Filters:
    start: date
    end: date  # inclusive
    channels: tuple[str, ...] = ()  # empty = all
    sources: tuple[str, ...] = ()
    teams: tuple[str, ...] = ()

    def where(self) -> tuple[str, list]:
        """SQL condition on alias ``f`` and its bound parameters."""
        clauses = ["f.date_day between ? and ?"]
        params: list = [self.start, self.end]
        for column, values in (
            ("channel", self.channels),
            ("lead_source", self.sources),
            ("team", self.teams),
        ):
            if values:
                clauses.append(f"list_contains(?::varchar[], f.{column})")
                params.append(list(values))
        return " and ".join(clauses), params

    def previous_period(self) -> Filters:
        """The period of the same length right before this one (for KPI deltas)."""
        length = (self.end - self.start).days + 1
        return Filters(
            self.start - timedelta(days=length),
            self.start - timedelta(days=1),
            self.channels,
            self.sources,
            self.teams,
        )


def _base(filters: Filters) -> tuple[str, list]:
    where, params = filters.where()
    return f"{metrics.BASE_FILTER} and {where}", params


def date_bounds(con: duckdb.DuckDBPyConnection) -> tuple[date, date]:
    lo, hi = con.execute(
        f"select min(date_day), max(date_day) from {LEADS_RELATION} as f "
        f"where {metrics.BASE_FILTER}"
    ).fetchone()
    return lo, hi


def options(con: duckdb.DuckDBPyConnection, column: str) -> list[str]:
    assert column in {"channel", "lead_source", "team"}
    rows = con.execute(f"select distinct {column} from {LEADS_RELATION} as f order by 1").fetchall()
    return [r[0] for r in rows]


def kpis(con: duckdb.DuckDBPyConnection, filters: Filters) -> pd.Series:
    """Every KPI of the metric layer for the filtered leads (one Series, keyed by metric)."""
    where, params = filters.where()
    sql = metrics.kpi_select(where).replace("marts.fct_leads", LEADS_RELATION)
    return con.execute(sql, params).df().iloc[0]


def funnel(con: duckdb.DuckDBPyConnection, filters: Filters) -> pd.DataFrame:
    """Nested funnel stages (each stage only counts leads that passed the previous ones)."""
    where, params = _base(filters)
    row = con.execute(
        f"""
        select
            count(*) as created,
            count(*) filter (where is_responded) as responded,
            count(*) filter (where is_responded and n_meetings > 0) as meeting_held,
            count(*) filter (where is_responded and n_meetings > 0 and is_converted) as converted
        from {LEADS_RELATION} as f
        where {where}
        """,
        params,
    ).fetchone()
    stages = ["created", "responded", "meeting held", "converted"]
    out = pd.DataFrame({"stage": stages, "leads": list(row)})
    out["step_conversion"] = out["leads"] / out["leads"].shift(1)
    out["cumulative_conversion"] = out["leads"] / out["leads"].iloc[0] if row[0] else np.nan
    return out


def wilson(successes: pd.Series, n: pd.Series, z: float = 1.96) -> tuple[pd.Series, pd.Series]:
    """95 % Wilson interval (same formula as analysis.eda.wilson_ci, kept dependency-free)."""
    n = n.astype(float)
    p = (successes / n).where(n > 0, 0.0)
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def by_dimension(con: duckdb.DuckDBPyConnection, filters: Filters, dim: str) -> pd.DataFrame:
    """Rates per channel / source / team with 95 % Wilson CIs and a small-sample flag."""
    assert dim in {"channel", "lead_source", "team"}
    where, params = _base(filters)
    t = con.execute(
        f"""
        select
            {dim} as grp,
            count(*) as n,
            count(*) filter (where is_converted) as conversions,
            count(is_sla_met) as sla_n,
            count(*) filter (where is_sla_met) as sla_met,
            median(minutes_to_first_response) filter (where not is_response_time_invalid)
                as median_response_min
        from {LEADS_RELATION} as f
        where {where}
        group by grp
        order by n desc
        """,
        params,
    ).df()
    t["conversion_rate"] = t["conversions"] / t["n"]
    t["conversion_lo"], t["conversion_hi"] = wilson(t["conversions"], t["n"])
    t["sla_rate"] = t["sla_met"] / t["sla_n"]
    t["sla_lo"], t["sla_hi"] = wilson(t["sla_met"], t["sla_n"])
    t["small_sample"] = t["n"] < SMALL_N
    return t


def weekly(con: duckdb.DuckDBPyConnection, filters: Filters) -> pd.DataFrame:
    """Leads and SLA rate per ISO week; partial weeks (fewer than 7 days) flagged."""
    where, params = _base(filters)
    return con.execute(
        f"""
        select
            iso_year,
            iso_week,
            min(date_day) as week_start,
            count(*) as leads,
            avg(is_sla_met::int) as sla_rate,
            avg(is_converted::int) as conversion_rate,
            count(distinct date_day) < 7 as is_partial
        from {LEADS_RELATION} as f
        where {where}
        group by iso_year, iso_week
        order by iso_year, iso_week
        """,
        params,
    ).df()


def weekday_hour(con: duckdb.DuckDBPyConnection, filters: Filters) -> pd.DataFrame:
    """Long table: ISO weekday × local hour → leads and SLA rate."""
    where, params = _base(filters)
    return con.execute(
        f"""
        select
            iso_day_of_week,
            hour(created_at_local) as local_hour,
            count(*) as leads,
            avg(is_sla_met::int) as sla_rate
        from {LEADS_RELATION} as f
        where {where}
        group by all
        order by 1, 2
        """,
        params,
    ).df()


def agents(con: duckdb.DuckDBPyConnection, filters: Filters) -> pd.DataFrame:
    """One row per agent and team (point-in-time team), with CIs and a small-sample flag."""
    where, params = _base(filters)
    t = con.execute(
        f"""
        select
            agent_id,
            team,
            count(*) as n,
            count(is_sla_met) as sla_n,
            count(*) filter (where is_sla_met) as sla_met,
            avg(is_converted::int) as conversion_rate,
            median(minutes_to_first_response) filter (where not is_response_time_invalid)
                as median_response_min
        from {LEADS_RELATION} as f
        where {where}
        group by all
        order by team, agent_id
        """,
        params,
    ).df()
    t["sla_rate"] = t["sla_met"] / t["sla_n"]
    t["sla_lo"], t["sla_hi"] = wilson(t["sla_met"], t["sla_n"])
    t["small_sample"] = t["n"] < SMALL_N
    return t


def reconcile_with_sql(con: duckdb.DuckDBPyConnection, sql_file) -> pd.DataFrame:
    """Compare the dashboard's unfiltered KPIs with Q1 of ``sql/analysis/01_funnel_kpis.sql``.

    Two independent implementations of the same definitions must agree; this is the
    check that the dashboard and the analytical SQL never drift apart.
    """
    text = sql_file.read_text(encoding="utf-8")
    q1 = text[text.index("-- Q1") : text.index("-- Q2")]
    sql_row = con.execute(q1.strip().rstrip(";")).df().iloc[0]
    lo, hi = date_bounds(con)
    dash = kpis(con, Filters(lo, hi))
    pairs = {
        "leads": ("leads", 0),
        "response_rate": ("response_rate", 4),
        "sla_rate": ("sla_rate", 4),
        "median_response_min": ("median_minutes_to_response", 1),
        "p90_response_min": ("p90_minutes_to_response", 1),
        "conversion_rate": ("conversion_rate", 4),
        "pipeline_eur": ("pipeline_value_eur", 0),
    }
    rows = []
    for key, (sql_col, digits) in pairs.items():
        d, s = round(float(dash[key]), digits), float(sql_row[sql_col])
        rows.append({"kpi": key, "dashboard": d, "sql_analysis": s, "match": d == s})
    return pd.DataFrame(rows)
