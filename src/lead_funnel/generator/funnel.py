"""Funnel simulation: first response, conversion, interactions and opportunities.

This module implements the causal model documented in ``docs/data/causal_dag.md``.
It also computes the *true* (counterfactual) quantities that real data never
reveals, so the analysis in F08 can be checked against them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lead_funnel.generator.entities import size_band
from lead_funnel.generator.params import ConversionParams, GeneratorParams

HOUR = pd.Timedelta(hours=1)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def standardised_score(lead_score: pd.Series) -> np.ndarray:
    """``s = (lead_score - 50) / 15``: the scale used by every model equation."""
    return (lead_score.to_numpy(dtype=float) - 50.0) / 15.0


# ----------------------------------------------------------------------------------
# First response
# ----------------------------------------------------------------------------------
def next_business_opening(
    created_at_utc: pd.Series, timezone: str, open_hour: int, close_hour: int
) -> pd.Series:
    """Earliest moment an agent can start working on each lead (Mon-Fri, local time).

    * inside business hours  -> the creation time itself
    * weekday before opening -> same day at ``open_hour``
    * after closing/weekend  -> next business day at ``open_hour``
    """
    local = created_at_utc.dt.tz_convert(timezone).dt.tz_localize(None)
    day = local.dt.normalize()
    hour = local.dt.hour.to_numpy()
    weekday = local.dt.day_of_week.to_numpy() < 5

    inside = weekday & (hour >= open_hour) & (hour < close_hour)
    before_open = weekday & (hour < open_hour)
    days = day.to_numpy().astype("datetime64[D]")
    next_day = np.busday_offset(days, np.where(weekday, 1, 0), roll="forward")
    open_day = np.where(before_open, days, next_day)
    opening = pd.Series(open_day.astype("datetime64[ns]"), index=local.index) + pd.Timedelta(
        hours=open_hour
    )
    start_local = local.where(inside, opening)
    return start_local.dt.tz_localize(timezone).dt.tz_convert("UTC")


def _daily_load(leads: pd.DataFrame, team: np.ndarray, timezone: str) -> np.ndarray:
    """Leads routed to the same team on the same local day, relative to that team's mean."""
    day = leads["created_at"].dt.tz_convert(timezone).dt.date
    counts = pd.Series(1, index=leads.index).groupby([day, team]).transform("sum")
    team_mean = counts.groupby(team).transform("mean")
    return (counts / team_mean).to_numpy()


def simulate_first_response(
    leads: pd.DataFrame,
    agents: pd.DataFrame,
    team: np.ndarray,
    gp: GeneratorParams,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """True first-response time per lead (NaT when the lead is never answered)."""
    rp, tz = gp.response, gp.volume.timezone
    s = standardised_score(leads["lead_score"])
    responded = rng.random(len(leads)) >= _sigmoid(
        rp.no_response_intercept + rp.no_response_slope * s
    )

    seniority = leads["owner_agent_id"].map(agents.groupby("agent_id")["seniority"].first())
    log_minutes = (
        leads["channel"].map(rp.channel_log_minutes).to_numpy(dtype=float)
        + seniority.map(rp.seniority).to_numpy(dtype=float)
        + rp.beta_score * s
        + rp.beta_load * np.log(_daily_load(leads, team, tz))
        + rng.normal(0.0, rp.sigma, len(leads))
    )
    start = next_business_opening(
        leads["created_at"], tz, rp.business_open_hour, rp.business_close_hour
    )
    first_response_at = (start + pd.to_timedelta(np.exp(log_minutes), unit="min")).dt.floor("s")
    first_response_at = first_response_at.where(responded)
    hours = (first_response_at - leads["created_at"]) / HOUR
    return pd.DataFrame(
        {
            "responded": responded,
            "first_response_at": first_response_at,
            "hours_to_first_response": hours.to_numpy(dtype=float),
        },
        index=leads.index,
    )


# ----------------------------------------------------------------------------------
# Conversion
# ----------------------------------------------------------------------------------
def conversion_logit(
    leads: pd.DataFrame,
    hours: np.ndarray,
    responded: np.ndarray,
    cp: ConversionParams,
) -> np.ndarray:
    """Linear predictor of the conversion model (see ``ConversionParams``)."""
    s = standardised_score(leads["lead_score"])
    band = pd.Series(size_band(leads["company_size"]), index=leads.index)
    response_term = np.where(
        responded,
        cp.beta_log2_hours * np.log2(1.0 + np.nan_to_num(hours, nan=0.0)),
        cp.no_response_effect,
    )
    return (
        cp.intercept
        + cp.beta_score * s
        + response_term
        + leads["channel"].map(cp.channel).to_numpy(dtype=float)
        + leads["source"].map(cp.source).to_numpy(dtype=float)
        + band.map(cp.size_band).to_numpy(dtype=float)
    )


def simulate_conversion(
    leads: pd.DataFrame, response: pd.DataFrame, gp: GeneratorParams, rng: np.random.Generator
) -> pd.DataFrame:
    """Observed conversion plus the true probabilities under observed and policy response."""
    cp = gp.conversion
    responded = response["responded"].to_numpy()
    hours = response["hours_to_first_response"].to_numpy()
    p_observed = _sigmoid(conversion_logit(leads, hours, responded, cp))

    # counterfactual: every lead answered after at most `policy_response_hours`
    policy_hours = np.where(
        responded, np.minimum(hours, cp.policy_response_hours), cp.policy_response_hours
    )
    p_policy = _sigmoid(conversion_logit(leads, policy_hours, np.ones(len(leads), dtype=bool), cp))
    converted = rng.random(len(leads)) < p_observed
    return pd.DataFrame(
        {"p_conversion": p_observed, "p_conversion_policy": p_policy, "converted": converted},
        index=leads.index,
    )


# ----------------------------------------------------------------------------------
# Opportunities and interactions
# ----------------------------------------------------------------------------------
def simulate_opportunities(
    leads: pd.DataFrame,
    response: pd.DataFrame,
    conversion: pd.DataFrame,
    gp: GeneratorParams,
    rng: np.random.Generator,
) -> pd.DataFrame:
    ap = gp.activity
    conv = conversion["converted"].to_numpy()
    base = response["first_response_at"].where(
        response["responded"], leads["created_at"] + pd.Timedelta(days=1)
    )[conv]
    lag = pd.to_timedelta(rng.exponential(ap.opportunity_lag_days_mean, conv.sum()), unit="D")
    band = size_band(leads.loc[conv, "company_size"])
    log_mean = pd.Series(band).map(ap.log_amount_by_size).to_numpy(dtype=float)
    opps = pd.DataFrame(
        {
            "lead_id": leads.loc[conv, "lead_id"].to_numpy(),
            "opened_at": (base + lag).dt.floor("s").to_numpy(),
            "amount_eur": np.round(np.exp(rng.normal(log_mean, ap.log_amount_sd)), 2),
        }
    )
    opps["opened_at"] = pd.to_datetime(opps["opened_at"], utc=True)
    opps = opps.sort_values(["opened_at", "lead_id"], ignore_index=True)
    opps.insert(0, "opportunity_id", [f"O{i:06d}" for i in range(1, len(opps) + 1)])
    return opps


def _first_contact_type(channel: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    p_call = pd.Series(channel).map(
        {"phone": 1.0, "web_form": 0.5, "email": 0.0, "partner_referral": 0.7}
    )
    return np.where(rng.random(len(channel)) < p_call.to_numpy(), "call", "email")


def simulate_interactions(
    leads: pd.DataFrame,
    response: pd.DataFrame,
    conversion: pd.DataFrame,
    opportunities: pd.DataFrame,
    gp: GeneratorParams,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Outbound contacts: first response, follow-ups and (for converted leads) a meeting."""
    ap = gp.activity
    ok = response["responded"].to_numpy()
    lead_id = leads["lead_id"].to_numpy()[ok]
    agent_id = leads["owner_agent_id"].to_numpy()[ok]
    # naive datetime64 in UTC: tz-aware Series.to_numpy() would give an object array
    first_at = response["first_response_at"].dt.tz_convert(None).to_numpy()[ok]
    converted = conversion["converted"].to_numpy()[ok]
    s = standardised_score(leads["lead_score"])[ok]

    parts = [
        pd.DataFrame(
            {
                "lead_id": lead_id,
                "agent_id": agent_id,
                "event_type": _first_contact_type(leads["channel"].to_numpy()[ok], rng),
                "occurred_at": first_at,
            }
        )
    ]

    lam = np.clip(
        ap.followups_base + ap.followups_if_converted * converted + ap.followups_per_score * s,
        0.05,
        None,
    )
    n_follow = np.minimum(rng.poisson(lam), ap.max_followups)
    rep = np.repeat(np.arange(len(lead_id)), n_follow)
    if len(rep):
        gaps = rng.exponential(ap.followup_gap_days_mean, len(rep))
        # cumulative gap within each lead: restart the running sum at every new lead
        cum = np.cumsum(gaps)
        starts = np.r_[0, np.cumsum(n_follow)[:-1]]
        offset_per_lead = np.r_[0.0, cum][starts]
        cum -= np.repeat(offset_per_lead[n_follow > 0], n_follow[n_follow > 0])
        parts.append(
            pd.DataFrame(
                {
                    "lead_id": lead_id[rep],
                    "agent_id": agent_id[rep],
                    "event_type": np.where(rng.random(len(rep)) < 0.5, "call", "email"),
                    "occurred_at": first_at[rep] + pd.to_timedelta(cum, unit="D").to_numpy(),
                }
            )
        )

    opened = opportunities.set_index("lead_id")["opened_at"]
    conv_ids = lead_id[converted]
    if len(conv_ids):
        first_conv = pd.Series(first_at[converted], index=conv_ids).dt.tz_localize("UTC")
        open_conv = opened.reindex(conv_ids)
        frac = rng.uniform(0.3, 0.9, len(conv_ids))
        meeting_at = first_conv + (open_conv - first_conv) * frac
        parts.append(
            pd.DataFrame(
                {
                    "lead_id": conv_ids,
                    "agent_id": agent_id[converted],
                    "event_type": "meeting",
                    "occurred_at": meeting_at.dt.tz_localize(None).to_numpy(),
                }
            )
        )

    events = pd.concat(parts, ignore_index=True)
    events["occurred_at"] = pd.to_datetime(events["occurred_at"]).dt.floor("s")
    if events["occurred_at"].dt.tz is None:
        events["occurred_at"] = events["occurred_at"].dt.tz_localize("UTC")

    mu = events["event_type"].map(ap.log_duration_s).to_numpy(dtype=float)
    sd = events["event_type"].map(ap.log_duration_sd).to_numpy(dtype=float)
    events["duration_s"] = np.round(np.exp(rng.normal(mu, sd))).astype("int64")
    lag = rng.exponential(ap.recording_lag_minutes_mean, len(events))
    events["recorded_at"] = (events["occurred_at"] + pd.to_timedelta(lag, unit="min")).dt.floor("s")

    events = events.sort_values(["occurred_at", "lead_id"], kind="stable", ignore_index=True)
    events.insert(0, "interaction_id", [f"I{i:07d}" for i in range(1, len(events) + 1)])
    return events[
        [
            "interaction_id",
            "lead_id",
            "agent_id",
            "event_type",
            "occurred_at",
            "recorded_at",
            "duration_s",
        ]
    ]


# ----------------------------------------------------------------------------------
# Ground truth summary
# ----------------------------------------------------------------------------------
def summarise_truth(
    response: pd.DataFrame, conversion: pd.DataFrame, sla_hours: float = 1.0
) -> dict[str, float]:
    """Realised true quantities that the analysis should recover (or be biased against)."""
    responded = response["responded"].to_numpy()
    hours = response["hours_to_first_response"].to_numpy()
    conv = conversion["converted"].to_numpy()
    p_obs = conversion["p_conversion"].to_numpy()
    p_pol = conversion["p_conversion_policy"].to_numpy()
    sla_met = responded & (hours <= sla_hours)
    missed = responded & (hours > sla_hours)
    return {
        "n_leads": int(len(conv)),
        "share_responded": float(responded.mean()),
        "share_sla_met": float(sla_met.mean()),
        "conversion_rate": float(conv.mean()),
        "mean_p_conversion_observed": float(p_obs.mean()),
        "mean_p_conversion_policy": float(p_pol.mean()),
        "true_policy_lift_pp": float(100 * (p_pol.mean() - p_obs.mean())),
        "true_effect_on_leads_missing_sla_pp": float(100 * (p_pol[missed] - p_obs[missed]).mean()),
        "naive_sla_gap_pp": float(100 * (conv[sla_met].mean() - conv[missed].mean())),
    }
