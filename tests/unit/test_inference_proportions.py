"""H1 machinery: two-proportion tests, intervals, effect sizes, analysis frame."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.proportion import proportions_ztest

from lead_funnel.analysis import inference as inf


def test_z_test_matches_statsmodels_and_chi2() -> None:
    t = inf.two_proportion_test(120, 500, 90, 600)
    z_ref, p_ref = proportions_ztest([120, 90], [500, 600])
    assert t.z == pytest.approx(z_ref)
    assert t.p_value == pytest.approx(p_ref)
    assert t.z**2 == pytest.approx(t.chi2)  # for a 2x2 table, z² = χ² (no continuity correction)
    assert t.chi2_p_value == pytest.approx(t.p_value)


def test_effect_sizes() -> None:
    t = inf.two_proportion_test(30, 100, 20, 100)
    assert t.diff == pytest.approx(0.10)
    assert t.relative_risk == pytest.approx(1.5)
    assert t.odds_ratio == pytest.approx((0.3 / 0.7) / (0.2 / 0.8))
    assert t.cohens_h == pytest.approx(2 * np.arcsin(np.sqrt(0.3)) - 2 * np.arcsin(np.sqrt(0.2)))
    assert t.diff_ci[0] < t.diff < t.diff_ci[1]
    assert t.p1_ci[0] < 0.3 < t.p1_ci[1]


def test_bootstrap_agrees_with_newcombe_for_large_samples() -> None:
    t = inf.two_proportion_test(2_000, 10_000, 1_500, 10_000)
    lo, hi = inf.bootstrap_diff_ci(t.x1, t.n1, t.x2, t.n2, resamples=20_000, seed=1)
    assert lo == pytest.approx(t.diff_ci[0], abs=0.002)
    assert hi == pytest.approx(t.diff_ci[1], abs=0.002)


@pytest.mark.parametrize(
    ("x1", "x2", "significant", "relevant"),
    [
        (2_150, 2_000, True, False),  # +1.5 pp, significant but below the +2 pp threshold
        (2_600, 2_000, True, True),  # +6 pp, CI entirely above 2 pp
        (2_010, 2_000, False, False),  # +0.1 pp, neither
    ],
)
def test_statistical_vs_practical_significance(x1, x2, significant, relevant) -> None:
    t = inf.two_proportion_test(x1, 10_000, x2, 10_000)
    assert (t.significant, t.practically_relevant) == (significant, relevant)


def test_analysis_frame() -> None:
    leads = pd.DataFrame(
        {
            "is_responded": [True, True, False, True, True],
            "minutes_to_first_response": [30.0, 180.0, np.nan, -10.0, 60 * 24 * 40],
            "is_response_time_invalid": [False, False, False, True, False],
            "is_response_time_outlier": [False, False, False, False, True],
            "is_sla_met": pd.array([True, False, False, pd.NA, False], dtype="boolean"),
            "is_converted": [True, False, False, True, False],
            "lead_score": [50, 70, 30, 40, 60],
            "iso_day_of_week": [1, 6, 3, 2, 2],
            "local_hour": [9, 9, 20, 10, 10],
        }
    )
    df = inf.analysis_frame(leads)
    assert len(df) == 3  # invalid and implausible response times excluded
    assert df["log2_hours"].tolist() == [pytest.approx(np.log2(1.5)), pytest.approx(2.0), 0.0]
    assert df["no_response"].tolist() == [0, 0, 1]
    assert df["sla_met"].tolist() == [True, False, False]
    assert df["business_hours"].tolist() == [True, False, False]
    assert len(inf.analysis_frame(leads, exclude_errors=False)) == 5
