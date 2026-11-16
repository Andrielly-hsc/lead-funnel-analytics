"""Behaviour of the funnel simulation and recovery of the true causal effect."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
import statsmodels.formula.api as smf

from lead_funnel.generator.core import GeneratedData
from lead_funnel.generator.entities import routed_team, size_band
from lead_funnel.generator.funnel import next_business_opening
from lead_funnel.generator.params import ConversionParams

TZ = "Europe/Berlin"


@pytest.mark.parametrize(
    ("local_created", "local_expected"),
    [
        ("2025-03-12 10:30", "2025-03-12 10:30"),  # Wednesday, inside business hours
        ("2025-03-12 06:15", "2025-03-12 08:00"),  # Wednesday, before opening
        ("2025-03-12 19:00", "2025-03-13 08:00"),  # Wednesday, after closing
        ("2025-03-14 18:00", "2025-03-17 08:00"),  # Friday at closing time -> Monday
        ("2025-03-15 11:00", "2025-03-17 08:00"),  # Saturday -> Monday
        ("2025-03-30 12:00", "2025-03-31 08:00"),  # Sunday of the DST switch -> Monday
    ],
)
def test_next_business_opening(local_created: str, local_expected: str) -> None:
    created = pd.Series([pd.Timestamp(local_created, tz=TZ).tz_convert("UTC")])
    got = next_business_opening(created, TZ, 8, 18).iloc[0]
    assert got == pd.Timestamp(local_expected, tz=TZ)


def test_first_interaction_is_the_true_first_response(clean_data: GeneratedData) -> None:
    truth = clean_data.truth_leads.set_index("lead_id")
    first = clean_data.tables["interactions"].groupby("lead_id")["occurred_at"].min()
    responded = truth.index[truth["responded"]]
    assert set(first.index) == set(responded)
    expected = truth.loc[first.index, "true_first_response_at"]
    assert (first == expected).all()


def test_opportunities_exist_exactly_for_converted_leads(clean_data: GeneratedData) -> None:
    truth = clean_data.truth_leads
    opps = clean_data.tables["opportunities"]
    assert set(opps["lead_id"]) == set(truth.loc[truth["converted"], "lead_id"])
    first = truth.set_index("lead_id")["true_first_response_at"].reindex(opps["lead_id"])
    answered = first.notna().to_numpy()
    assert (opps["opened_at"].to_numpy()[answered] >= first.to_numpy()[answered]).all()


def test_leads_are_routed_to_an_agent_of_the_right_team(clean_data: GeneratedData) -> None:
    leads, agents = clean_data.tables["leads"], clean_data.tables["agents"]
    day = leads["created_at"].dt.tz_convert(TZ).dt.tz_localize(None).dt.normalize()
    merged = leads.assign(day=day, expected=routed_team(leads)).merge(
        agents, left_on="owner_agent_id", right_on="agent_id"
    )
    valid_to = merged["valid_to"].fillna(pd.Timestamp("2200-01-01"))
    active = merged[(merged["valid_from"] <= merged["day"]) & (merged["day"] < valid_to)]
    assert len(active) == len(leads)  # exactly one active version per lead
    assert (active["team"] == active["expected"]).all()


def _model_frame(data: GeneratedData) -> pd.DataFrame:
    leads = data.tables["leads"]
    truth = data.truth_leads
    return pd.DataFrame(
        {
            "converted": truth["converted"].astype(int),
            "log2_hours": np.log2(1 + truth["true_hours_to_first_response"].fillna(0)),
            "no_response": (~truth["responded"]).astype(int),
            "s": (leads["lead_score"] - 50) / 15,
            "channel": leads["channel"],
            "source": leads["source"],
            "band": size_band(leads["company_size"]),
        }
    )


def test_adjusted_regression_recovers_the_true_effect(clean_data: GeneratedData) -> None:
    """With the right adjustment set, the estimate is within 3 standard errors of the truth."""
    d = _model_frame(clean_data)
    model = smf.logit(
        "converted ~ s + log2_hours + no_response + C(channel) + C(source) + C(band)", d
    ).fit(disp=0)
    true_beta = ConversionParams().beta_log2_hours
    est, se = model.params["log2_hours"], model.bse["log2_hours"]
    assert abs(est - true_beta) < 3 * se, f"estimate {est:.4f} ± {se:.4f}, truth {true_beta:.4f}"
    assert abs(model.params["s"] - ConversionParams().beta_score) < 3 * model.bse["s"]


def test_omitting_the_confounder_overstates_the_effect(clean_data: GeneratedData) -> None:
    d = _model_frame(clean_data)
    naive = smf.logit("converted ~ log2_hours + no_response", d).fit(disp=0)
    assert naive.params["log2_hours"] < ConversionParams().beta_log2_hours  # more negative


def test_naive_sla_gap_is_larger_than_the_true_effect(clean_data: GeneratedData) -> None:
    realised = clean_data.ground_truth["realised"]
    assert realised["naive_sla_gap_pp"] > 1.5 * realised["true_effect_on_leads_missing_sla_pp"]
    assert realised["true_policy_lift_pp"] > 0


def test_conversion_probabilities_are_calibrated(clean_data: GeneratedData) -> None:
    truth = clean_data.truth_leads
    observed, expected = truth["converted"].mean(), truth["p_conversion"].mean()
    se = math.sqrt(expected * (1 - expected) / len(truth))
    assert abs(observed - expected) < 4 * se
