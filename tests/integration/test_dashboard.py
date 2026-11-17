"""Dashboard queries, reconciliation with the analytical SQL, and the app itself."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest

from lead_funnel.dashboard import queries as q

pytestmark = pytest.mark.integration
REPO_ROOT = Path(__file__).resolve().parents[2]
APP = REPO_ROOT / "src" / "lead_funnel" / "dashboard" / "app.py"


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A small marts schema with the columns the dashboard reads (600 leads, 8 weeks)."""
    rng = np.random.default_rng(0)
    n = 600
    days = pd.date_range("2025-03-03", periods=56, freq="D")
    day = rng.choice(days, n)
    responded = rng.random(n) < 0.95
    minutes = np.where(responded, rng.exponential(90, n), np.nan)
    invalid = np.zeros(n, dtype=bool)
    invalid[:3] = True
    minutes[:3] = -10
    fct = pd.DataFrame(
        {
            "channel_key": rng.choice(["c1", "c2", "c3"], n),
            "lead_source_key": rng.choice(["s1", "s2"], n),
            "owner_agent_key": rng.choice(["a1", "a2", "a3"], n),
            "created_date_key": [int(d.strftime("%Y%m%d")) for d in pd.DatetimeIndex(day)],
            "created_at_local": pd.DatetimeIndex(day)
            + pd.to_timedelta(rng.integers(0, 24, n), "h"),
            "is_probable_duplicate": rng.random(n) < 0.02,
            "is_responded": responded,
            "is_sla_met": pd.array(
                np.where(invalid, None, responded & (minutes <= 60)), dtype="boolean"
            ),
            "minutes_to_first_response": minutes,
            "is_response_time_invalid": invalid,
            "is_converted": rng.random(n) < 0.15,
            "n_touches": rng.integers(0, 5, n),
        }
    )
    fct["n_meetings"] = (fct["is_converted"] & fct["is_responded"]).astype(int)
    fct["opportunity_amount_eur"] = np.where(fct["is_converted"], rng.uniform(1e3, 5e4, n), np.nan)
    dim_date = pd.DataFrame({"date_day": pd.date_range("2025-01-01", "2025-12-31").date})
    dd = pd.DatetimeIndex(dim_date["date_day"])
    dim_date["date_key"] = [int(d.strftime("%Y%m%d")) for d in dd]
    iso = dd.isocalendar()
    dim_date["iso_year"], dim_date["iso_week"] = iso["year"].to_numpy(), iso["week"].to_numpy()
    dim_date["iso_day_of_week"] = iso["day"].to_numpy()

    path = tmp_path_factory.mktemp("dash") / "wh.duckdb"
    con = duckdb.connect(str(path))
    con.execute("create schema marts")
    for name, df in {
        "fct_leads": fct,
        "dim_date": dim_date,
        "dim_channel": pd.DataFrame(
            {"channel_key": ["c1", "c2", "c3"], "channel": ["web_form", "email", "phone"],
             "channel_label": ["Web form", "E-mail", "Phone"]}
        ),
        "dim_lead_source": pd.DataFrame(
            {"lead_source_key": ["s1", "s2"], "lead_source": ["organic_search", "event"],
             "lead_source_label": ["Organic search", "Event"]}
        ),
        "dim_agent": pd.DataFrame(
            {"agent_key": ["a1", "a2", "a3"], "agent_id": ["A1", "A2", "A3"],
             "team": ["inbound_dach", "inbound_dach", "partner"]}
        ),
    }.items():  # fmt: skip
        con.register("df", df)
        con.execute(f"create table marts.{name} as select * from df")
        con.unregister("df")
    con.close()
    return path


@pytest.fixture
def con(warehouse: Path):
    c = duckdb.connect(str(warehouse), read_only=True)
    yield c
    c.close()


def test_filters_use_bound_parameters_and_previous_period() -> None:
    f = q.Filters(date(2025, 3, 1), date(2025, 3, 10), channels=("phone",), teams=("partner",))
    where, params = f.where()
    assert "phone" not in where and where.count("?") == len(params) == 4
    prev = f.previous_period()
    assert (prev.start, prev.end) == (date(2025, 2, 19), date(2025, 2, 28))
    assert prev.channels == ("phone",)


def test_options_bounds_and_filtered_kpis(con) -> None:
    lo, hi = q.date_bounds(con)
    assert date(2025, 3, 3) <= lo <= hi <= date(2025, 4, 27)
    assert q.options(con, "team") == ["inbound_dach", "partner"]
    all_leads = q.kpis(con, q.Filters(lo, hi))
    phone = q.kpis(con, q.Filters(lo, hi, channels=("phone",)))
    assert 0 < phone["leads"] < all_leads["leads"] < 600  # duplicates excluded
    assert q.kpis(con, q.Filters(lo, hi).previous_period())["leads"] == 0


def test_funnel_is_nested(con) -> None:
    f = q.funnel(con, q.Filters(*q.date_bounds(con)))
    assert list(f["stage"]) == ["created", "responded", "meeting held", "converted"]
    assert f["leads"].is_monotonic_decreasing
    assert (f["step_conversion"].dropna() <= 1).all()


def test_by_dimension_intervals_and_small_samples(con) -> None:
    lo, hi = q.date_bounds(con)
    t = q.by_dimension(con, q.Filters(lo, hi), "channel")
    assert (t["sla_lo"] <= t["sla_rate"]).all() and (t["sla_rate"] <= t["sla_hi"]).all()
    assert not t["small_sample"].any()  # ~190 leads per channel
    one_week = q.by_dimension(con, q.Filters(lo, lo + pd.Timedelta(days=6)), "channel")
    assert one_week["small_sample"].all()


def test_weekly_weekday_hour_and_agents(con) -> None:
    lo, hi = q.date_bounds(con)
    f = q.Filters(lo, hi)
    w = q.weekly(con, f)
    assert len(w) == 8 and not w["is_partial"].any()
    grid = q.weekday_hour(con, f)
    assert grid["iso_day_of_week"].between(1, 7).all() and grid["local_hour"].between(0, 23).all()
    a = q.agents(con, f)
    assert set(a["agent_id"]) == {"A1", "A2", "A3"}


def test_dashboard_reconciles_with_the_analytical_sql(con) -> None:
    t = q.reconcile_with_sql(con, REPO_ROOT / "sql" / "analysis" / "01_funnel_kpis.sql")
    assert t["match"].all(), t[~t["match"]]


def test_app_renders_and_warns_on_small_selections(warehouse: Path, monkeypatch) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("LF_DB_PATH", str(warehouse))
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert [m.label for m in at.metric][:3] == ["Leads", "Response rate", "SLA met"]
    assert [t.label for t in at.tabs] == [
        "Overview",
        "Funnel",
        "SLA & response time",
        "Teams & agents",
        "Definitions",
    ]
    # full period: ~200 leads per agent, so no small-sample warning yet
    assert not any("fewer than 100 leads" in w.value for w in at.warning)

    start = at.sidebar.date_input[0].value[0]
    at.sidebar.date_input[0].set_value((start, start)).run()  # a single day
    assert not at.exception
    warnings = " ".join(w.value for w in at.warning)
    assert "too uncertain" in warnings  # the whole selection is small
    assert "fewer than 100 leads" in warnings  # and so is every agent


@pytest.mark.parametrize(
    ("p_now", "n_now", "p_before", "n_before", "noise"),
    [
        (0.416, 4_000, 0.412, 4_000, True),  # 0.4 pp on 4 000 leads: noise
        (0.45, 4_000, 0.40, 4_000, False),  # 5 pp on 4 000 leads: real change
        (0.60, 20, 0.40, 20, True),  # 20 pp on 20 leads: still noise
        (0.5, 0, 0.4, 100, True),  # no data
    ],
)
def test_change_is_noise(p_now, n_now, p_before, n_before, noise) -> None:
    assert q.change_is_noise(p_now, n_now, p_before, n_before) is noise


def test_app_explains_uncertainty(warehouse: Path, monkeypatch) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("LF_DB_PATH", str(warehouse))
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    text = " ".join(m.value for m in at.markdown)
    assert "How to read the uncertainty" in text and "Association, not cause" in text
    first = at.sidebar.date_input[0].value[0]
    # a later sub-period has a previous period inside the data, so deltas appear
    at.sidebar.date_input[0].set_value(
        (first + pd.Timedelta(days=28), first + pd.Timedelta(days=55))
    )
    at.run()
    assert not at.exception
    deltas = [m for m in at.metric if m.delta]
    assert deltas, "deltas expected when a previous period exists"
    assert any("grey deltas" in c.value for c in at.caption)
