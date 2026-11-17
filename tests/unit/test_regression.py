"""H3: naïve vs adjusted logistic models, g-computation and comparison with the truth."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lead_funnel.analysis import inference as inf
from lead_funnel.analysis import regression as reg
from lead_funnel.generator.core import GeneratedData, generate
from tests.factories import small_params


@pytest.fixture(scope="module")
def generated() -> GeneratedData:
    return generate(small_params(15_000), seed=11, clean=True)


@pytest.fixture(scope="module")
def frame(generated: GeneratedData) -> pd.DataFrame:
    return inf.analysis_frame(inf.leads_from_generated(generated))


@pytest.fixture(scope="module")
def models(frame: pd.DataFrame):
    return reg.fit(reg.NAIVE_HOURS, frame), reg.fit(reg.ADJUSTED, frame)


def test_frame_from_generator_has_the_model_columns(frame: pd.DataFrame) -> None:
    for col in ("converted", "log2_hours", "no_response", "lead_score_10", "sla_met"):
        assert col in frame
    assert len(frame) == 15_000


def test_adjustment_moves_the_estimate_towards_the_truth(models, generated) -> None:
    naive, adjusted = models
    true_beta = generated.ground_truth["params"]["conversion"]["beta_log2_hours"]
    b_naive = reg.coefficient(naive, "log2_hours")
    b_adj = reg.coefficient(adjusted, "log2_hours")
    assert b_naive.estimate < b_adj.estimate  # confounding exaggerates the effect
    assert abs(b_adj.estimate - true_beta) < abs(b_naive.estimate - true_beta)
    assert abs(b_adj.estimate - true_beta) < 3 * b_adj.se
    assert b_adj.odds_ratio == pytest.approx(np.exp(b_adj.estimate))


def test_policy_frame_only_changes_response_time(frame: pd.DataFrame) -> None:
    cf = reg.policy_frame(frame)
    assert (cf["no_response"] == 0).all()
    assert cf["log2_hours"].max() <= np.log2(1.5) + 1e-12
    fast = (frame["no_response"] == 0) & (frame["hours"] <= reg.POLICY_HOURS)
    assert np.allclose(cf.loc[fast, "log2_hours"], frame.loc[fast, "log2_hours"])
    pd.testing.assert_series_equal(cf["lead_score_10"], frame["lead_score_10"])


def test_g_computation_close_to_the_true_policy_effect(models, frame, generated) -> None:
    eff = reg.g_computation(models[1], frame)
    realised = generated.ground_truth["realised"]
    assert eff.lift_pp > 0 and eff.effect_on_missed_pp > eff.lift_pp
    assert eff.lift_pp == pytest.approx(realised["true_policy_lift_pp"], abs=1.0)


def test_marginal_effect_vif_and_calibration(models, frame) -> None:
    ame, lo, hi = reg.average_marginal_effect(models[1], "log2_hours")
    assert lo < ame < hi < 0
    vif = reg.vif_table(frame).set_index("term")["vif"]
    assert vif["log2_hours"] < 2
    cal = reg.calibration_table(models[1], frame)
    assert (cal["predicted"] - cal["observed"]).abs().max() < 0.05


def test_binned_model_is_monotone(frame: pd.DataFrame) -> None:
    t = reg.binned_model_table(frame).set_index("response_bin")["odds_ratio"]
    assert t["≤ 1 h"] == 1.0
    assert t["1-4 h"] > t["4-24 h"] > t["> 24 h"] > t["never answered"]


def test_stratification_shrinks_the_confounded_gap(frame: pd.DataFrame) -> None:
    s = reg.stratified_gap(frame)
    assert len(s) == 5
    assert s.attrs["stratified_gap_pp"] < s.attrs["crude_gap_pp"]


def test_comparison_table_and_figure(models, frame, generated, tmp_path: Path) -> None:
    naive, adjusted = models
    boot = reg.bootstrap_policy(frame, resamples=5, seed=1)
    assert len(boot) == 5
    eff = reg.g_computation(adjusted, frame)
    h1 = inf.sla_conversion_test(frame)
    table = reg.compare_with_truth(
        (100 * h1.diff, 100 * h1.diff_ci[0], 100 * h1.diff_ci[1]),
        reg.coefficient(naive, "log2_hours"),
        reg.coefficient(adjusted, "log2_hours"),
        eff,
        boot,
        generated.ground_truth,
    )
    assert list(table["label"]) == [
        "naïve",
        "adjusted",
        "missed SLA: naïve gap",
        "missed SLA: adjusted",
        "all within 30 min: adjusted",
    ]
    assert not table.loc[0, "truth_in_ci"]  # the naïve odds ratio misses the truth
    assert table.loc[2, "estimate"] > table.loc[3, "estimate"]  # adjustment shrinks the gap
    out = reg.plot_effect_comparison(table, tmp_path / "effect.png")
    assert out.exists() and out.stat().st_size > 10_000


def test_bootstrap_skips_and_counts_non_converged_resamples(frame, monkeypatch) -> None:
    real_fit = reg.fit
    calls = {"n": 0}

    def flaky_fit(formula, df):
        calls["n"] += 1
        if calls["n"] % 5 == 0:  # every fifth resample "separates"
            raise reg.ModelDidNotConverge("separation")
        return real_fit(formula, df)

    monkeypatch.setattr(reg, "fit", flaky_fit)
    boot = reg.bootstrap_policy(frame, resamples=10, seed=3)
    assert (len(boot), boot.attrs["failed"], boot.attrs["resamples"]) == (8, 2, 10)


def test_bootstrap_refuses_when_too_many_resamples_fail(frame, monkeypatch) -> None:
    def always_fails(formula, df):
        raise reg.ModelDidNotConverge("separation")

    monkeypatch.setattr(reg, "fit", always_fails)
    with pytest.raises(reg.ModelDidNotConverge, match="bootstrap resamples"):
        reg.bootstrap_policy(frame, resamples=5)
