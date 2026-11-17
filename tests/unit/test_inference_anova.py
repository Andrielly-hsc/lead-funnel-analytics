"""Correlation and one-way ANOVA with assumption checks."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from lead_funnel.analysis import inference as inf


def test_spearman_sees_a_monotonic_relation_pearson_understates() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(size=2_000)
    df = pd.DataFrame({"x": x, "y": np.exp(3 * x)})  # monotonic but very non-linear
    row = inf.correlation_table(df, ["x", "y"]).iloc[0]
    assert row["spearman_rho"] == pytest.approx(1.0)
    assert row["pearson_r"] < 0.6


def _groups(means, sds, n=400, seed=1) -> tuple[pd.Series, pd.Series]:
    rng = np.random.default_rng(seed)
    values = np.concatenate([rng.normal(m, s, n) for m, s in zip(means, sds, strict=True)])
    labels = np.repeat([f"g{i}" for i in range(len(means))], n)
    return pd.Series(values), pd.Series(labels)


def test_anova_matches_scipy_and_detects_a_real_difference() -> None:
    values, groups = _groups([0, 0, 1], [1, 1, 1])
    r = inf.one_way_anova(values, groups)
    f_ref, p_ref = stats.f_oneway(*[values[groups == g] for g in ("g0", "g1", "g2")])
    assert r.f == pytest.approx(f_ref) and r.f_p == pytest.approx(p_ref)
    # the decision rule, not a particular sample: Levene can reject by chance (5 % of samples
    # even when population variances are equal), and then Welch must be chosen
    assert r.recommended_test == ("welch" if r.levene_p < 0.05 else "classic")
    assert r.recommended_p < 0.001
    assert 0.1 < r.eta_squared < 0.3 and r.omega_squared < r.eta_squared
    pairs = r.tukey.set_index(["group1", "group2"])["reject"]
    assert not pairs[("g0", "g1")] and pairs[("g0", "g2")] and pairs[("g1", "g2")]


def test_anova_null_is_not_rejected() -> None:
    values, groups = _groups([5, 5, 5], [2, 2, 2], seed=7)
    r = inf.one_way_anova(values, groups)
    assert r.recommended_p > 0.05
    assert abs(r.omega_squared) < 0.01


def test_unequal_variances_switch_to_welch() -> None:
    values, groups = _groups([0, 0.2, 0], [0.5, 1, 4])
    r = inf.one_way_anova(values, groups)
    assert r.levene_p < 0.05
    assert r.recommended_test == "welch" and r.recommended_p == r.welch_p


def test_summary_and_qq_plot(tmp_path: Path) -> None:
    values, groups = _groups([1, 2], [0.3, 0.3])
    r = inf.one_way_anova(values.abs() + 0.1, groups)
    table = inf.anova_summary({"h": r})
    assert table.loc[0, "reject_H0"]
    out = inf.plot_qq(values.abs() + 0.1, groups, tmp_path / "qq.png", title="t")
    assert out.exists() and out.stat().st_size > 10_000
