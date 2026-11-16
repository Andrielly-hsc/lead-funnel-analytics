"""Anomaly detection and missingness helpers of analysis/eda.py."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lead_funnel.analysis import eda


def test_iqr_fences() -> None:
    lo, hi = eda.iqr_fences(pd.Series([1, 2, 3, 4, 5, 6, 7, 8]))
    # Q1 2.75, Q3 6.25, IQR 3.5 -> 2.75 - 1.5 * 3.5 = -2.5 and 6.25 + 1.5 * 3.5 = 11.5
    assert (lo, hi) == (-2.5, 11.5)


def test_robust_z_ignores_the_outlier_it_detects() -> None:
    s = pd.Series([10, 11, 9, 10, 12, 8, 10, 1000])
    z = eda.robust_z(s)
    assert z.iloc[-1] > 100  # the outlier stands out
    assert z.iloc[:-1].abs().max() < 2
    classic = (s - s.mean()) / s.std()
    assert classic.iloc[-1] < 3  # the classical z-score is dragged by the outlier itself


def test_raw_iqr_over_flags_skewed_data() -> None:
    rng = np.random.default_rng(1)
    minutes = pd.Series(np.exp(rng.normal(4, 1.5, 20_000)))  # log-normal, no errors at all
    table = eda.outlier_method_comparison(minutes).set_index("rule")["share"]
    assert table["IQR fence on raw minutes"] > 0.05
    assert table["IQR fence on log10(minutes)"] < 0.01


@pytest.fixture
def leads() -> pd.DataFrame:
    rng = np.random.default_rng(2)
    n = 200
    minutes = np.exp(rng.normal(4, 1, n))
    minutes[:3] = [-10.0, -2.0, 60 * 24 * 45]  # two clock-skew errors, one 45-day delay
    return pd.DataFrame(
        {
            "lead_id": [f"L{i}" for i in range(n)],
            "is_responded": True,
            "minutes_to_first_response": minutes,
            "is_response_time_invalid": minutes < 0,
            "is_response_time_outlier": minutes > 60 * 24 * 30,
            "channel": ["web_form"] * 100 + ["phone"] * 100,
            "company_size": [np.nan] * 25 + [10] * 75 + [np.nan] * 3 + [10] * 97,
        }
    )


def test_classify_response_times(leads: pd.DataFrame) -> None:
    classes = eda.classify_response_times(leads)
    assert classes.iloc[0] == classes.iloc[1] == "impossible (negative)"
    assert classes.iloc[2] == "implausible (> 30 days)"
    assert (classes.iloc[3:] != "impossible (negative)").all()


def test_detection_vs_injected(leads: pd.DataFrame) -> None:
    injected = {"negative_response_lead_ids": ["L0", "L1"], "extreme_delay_lead_ids": ["L2", "L9"]}
    t = eda.detection_vs_injected(leads, injected).set_index("flag")
    assert t.loc["is_response_time_invalid", ["precision", "recall"]].tolist() == [1.0, 1.0]
    assert t.loc["is_response_time_outlier", "recall"] == 0.5  # L9 was not detected


def test_missingness_by_group(leads: pd.DataFrame) -> None:
    m = eda.missingness_by(leads, "company_size", "channel")
    assert m["share"].to_dict() == {"web_form": 0.25, "phone": 0.03}
    assert (m["lo"] < m["share"]).all() and (m["share"] < m["hi"]).all()


def test_anomaly_figure(tmp_path: Path) -> None:
    rng = np.random.default_rng(3)
    n = 400
    channels = rng.choice(["web_form", "email", "phone", "partner_referral"], n)
    df = pd.DataFrame(
        {
            "is_responded": True,
            "is_response_time_invalid": False,
            "minutes_to_first_response": np.exp(rng.normal(4, 1.5, n)),
            "channel": channels,
            "company_size": np.where(rng.random(n) < 0.2, np.nan, 50),
        }
    )
    out = eda.plot_anomalies(df, tmp_path / "a.png")
    assert out.exists() and out.stat().st_size > 10_000
