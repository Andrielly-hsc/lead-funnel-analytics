"""Multiple-testing corrections, sensitivity analysis and the multi-seed study."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lead_funnel.analysis import inference as inf
from lead_funnel.analysis import robustness as rob
from lead_funnel.generator.core import generate
from tests.factories import small_params


@pytest.fixture(scope="module")
def leads() -> pd.DataFrame:
    df = inf.leads_from_generated(generate(small_params(12_000), seed=5, clean=True))
    return df.assign(team="t", is_response_time_invalid=False, is_response_time_outlier=False)


def test_corrections_are_never_less_conservative(leads: pd.DataFrame) -> None:
    seg = rob.segment_tests(inf.analysis_frame(leads), segments=("channel", "lead_source"))
    assert len(seg) == 4 + 6
    assert (seg["p_holm"] >= seg["p_value"] - 1e-15).all()
    assert (seg["p_bh"] >= seg["p_value"] - 1e-15).all()
    assert (seg["p_holm"] >= seg["p_bh"] - 1e-15).all()  # Holm is stricter than BH
    assert seg["sig_holm"].sum() <= seg["sig_bh"].sum() <= seg["sig_value"].sum()


def test_holm_and_bh_on_known_p_values() -> None:
    df = pd.DataFrame({"p": [0.001, 0.01, 0.02, 0.04, 0.3]})
    from statsmodels.stats.multitest import multipletests

    holm = multipletests(df["p"], method="holm")[1]
    assert holm[0] == pytest.approx(0.005)  # 0.001 * 5
    assert holm[3] == pytest.approx(0.08)  # step-down: 0.04 * 2 = 0.08 -> not significant


def test_sensitivity_table(leads: pd.DataFrame) -> None:
    t = rob.sensitivity_table(leads).set_index("variant")
    assert list(t.index) == [
        "primary (SLA 60 min)",
        "SLA 30 min",
        "SLA 120 min",
        "errors included (239 leads)",
        "business hours only",
    ]
    # the model does not depend on the SLA threshold; only the "missed" population does
    assert t.loc["SLA 30 min", "odds_ratio"] == t.loc["primary (SLA 60 min)", "odds_ratio"]
    assert t.loc["SLA 30 min", "effect_on_missed_pp"] < t.loc["SLA 120 min", "effect_on_missed_pp"]
    assert (t["odds_ratio"] < 1).all()


def test_seed_study_summary_and_plot(tmp_path: Path) -> None:
    study = rob.seed_study([1, 2], n_leads=10_000)
    assert list(study["seed"]) == [1, 2]
    assert (study["beta_true"] == study["beta_true"].iloc[0]).all()  # same truth, every seed
    summary = rob.seed_study_summary(study).set_index("quantity")
    assert summary.loc["beta", "mean_error"] == pytest.approx(
        (study["beta"] - study["beta_true"]).mean()
    )
    assert summary.attrs["seeds"] == 2
    assert 0 <= summary.attrs["beta_coverage"] <= 1
    out = rob.plot_seed_study(study, tmp_path / "s.png", highlight=("x", -0.18, -0.2, -0.16))
    assert out.exists() and out.stat().st_size > 10_000
    assert np.isfinite(study[["effect_on_missed_pp", "policy_lift_pp"]]).all().all()


def test_non_converged_models_are_refused() -> None:
    """Zero conversions among never-answered leads: quasi-complete separation."""
    from lead_funnel.analysis import regression as reg

    rng = np.random.default_rng(0)
    n = 2_000
    df = pd.DataFrame(
        {
            "no_response": (rng.random(n) < 0.1).astype(int),
            "log2_hours": rng.exponential(1, n),
        }
    )
    df["converted"] = np.where(df["no_response"] == 1, 0, (rng.random(n) < 0.3).astype(int))
    with pytest.raises(reg.ModelDidNotConverge, match="separation"):
        reg.fit("converted ~ log2_hours + no_response", df)
