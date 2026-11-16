"""Group and period comparisons of analysis/eda.py."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lead_funnel.analysis import eda


def test_wilson_ci_known_values_and_bounds() -> None:
    lo, hi = eda.wilson_ci(50, 100)
    assert (round(float(lo), 4), round(float(hi), 4)) == (0.4038, 0.5962)
    lo0, hi0 = eda.wilson_ci(0, 10)  # Wald would give [0, 0]; Wilson stays informative
    assert float(lo0) == pytest.approx(0, abs=1e-12) and 0.2 < float(hi0) < 0.35
    lo1, hi1 = eda.wilson_ci(10, 10)
    assert float(hi1) <= 1.0


def test_wilson_ci_narrows_with_more_data() -> None:
    small = np.subtract(*reversed(eda.wilson_ci(20, 100)))
    large = np.subtract(*reversed(eda.wilson_ci(2000, 10_000)))
    assert large < small / 5


@pytest.fixture
def leads() -> pd.DataFrame:
    t = pd.Timestamp("2025-03-03 09:00")  # a Monday
    return pd.DataFrame(
        {
            "lead_id": ["L1", "L2", "L3", "L4", "L5"],
            "channel": ["phone", "phone", "email", "email", "email"],
            "agent_id": ["A1", "A1", "A1", "A2", "A2"],
            "team": ["t_old", "t_old", "t_new", "t_x", "t_x"],
            "is_converted": [True, False, False, False, True],
            "is_sla_met": pd.array([True, True, False, pd.NA, False], dtype="boolean"),
            "minutes_to_first_response": [10.0, 30.0, 120.0, -5.0, 300.0],
            "created_at_local": [t, t + pd.Timedelta(days=1), t + pd.Timedelta(days=8),
                                 t, t + pd.Timedelta(hours=10)],
            "iso_year": [2025] * 5,
            "iso_week": [10, 10, 11, 10, 10],
            "iso_day_of_week": [1, 2, 2, 1, 1],
            "local_hour": [9, 9, 9, 9, 19],
        }
    )  # fmt: skip


def test_compare_groups_rates_and_valid_sla_denominator(leads: pd.DataFrame) -> None:
    t = eda.compare_groups(leads, "channel")
    assert t.loc["phone", ["n", "conversions", "sla_met"]].tolist() == [2, 1, 2]
    assert t.loc["email", "sla_n"] == 2  # the null SLA flag (invalid time) is not counted
    assert t.loc["email", "sla_rate"] == 0.0
    assert (t["conversion_lo"] <= t["conversion_rate"]).all()
    assert (t["conversion_rate"] <= t["conversion_hi"]).all()


def test_weekly_trend_flags_partial_weeks(leads: pd.DataFrame) -> None:
    w = eda.weekly_trend(leads)
    assert w["leads"].tolist() == [4, 1]
    assert w["is_partial"].all()  # 2 and 1 observed days
    assert w["week_start"].tolist() == [pd.Timestamp("2025-03-03"), pd.Timestamp("2025-03-10")]


def test_weekday_hour_is_a_full_7_by_24_grid(leads: pd.DataFrame) -> None:
    m = eda.weekday_hour(leads, "leads")
    assert m.shape == (7, 24)
    assert m.loc[1, 9] == 2 and m.loc[1, 19] == 1 and m.loc[7, 0] == 0
    sla = eda.weekday_hour(leads, "sla")
    assert np.isnan(sla.loc[7, 0])  # no data is "unknown", not 0 %


def test_team_change_comparison(leads: pd.DataFrame) -> None:
    t = eda.team_change_comparison(leads)
    assert t["agent_id"].unique().tolist() == ["A1"]  # A2 never changed team
    assert t.set_index("period")["team"].to_dict() == {"before": "t_old", "after": "t_new"}


@pytest.mark.parametrize("plot", [eda.plot_group_comparison, eda.plot_periods])
def test_figures_render(plot, tmp_path: Path) -> None:
    rng = np.random.default_rng(0)
    n = 400
    t0 = pd.Timestamp("2025-03-03")
    df = pd.DataFrame(
        {
            "lead_id": [f"L{i}" for i in range(n)],
            "channel": rng.choice(["web_form", "email", "phone", "partner_referral"], n),
            "lead_source": rng.choice(
                ["organic_search", "paid_search", "social", "event", "partner", "direct"], n
            ),
            "is_converted": rng.random(n) < 0.2,
            "is_sla_met": pd.array(rng.random(n) < 0.4, dtype="boolean"),
            "minutes_to_first_response": rng.exponential(60, n),
            "created_at_local": t0 + pd.to_timedelta(rng.integers(0, 28 * 24, n), unit="h"),
        }
    )
    iso = df["created_at_local"].dt.isocalendar()
    df["iso_year"], df["iso_week"] = iso["year"].astype(int), iso["week"].astype(int)
    df["iso_day_of_week"] = iso["day"].astype(int)
    df["local_hour"] = df["created_at_local"].dt.hour
    out = plot(df, tmp_path / "fig.png")
    assert out.exists() and out.stat().st_size > 10_000
