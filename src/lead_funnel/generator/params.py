"""Parameters of the synthetic CRM — the *ground truth* the analysis must recover.

Everything the generator assumes lives here, in one place, so that:

* the causal model is documented in code (see ``docs/data/causal_dag.md``);
* the true effects can be written to ``_ground_truth.json`` and compared with the
  estimates produced in F08;
* sensitivity analyses only need a different ``GeneratorParams`` instance.

All dataclasses are frozen: parameters are values, never mutated during a run.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from types import MappingProxyType


def _frozen(d: dict) -> Mapping:
    """Read-only dict, so frozen dataclasses stay truly immutable."""
    return MappingProxyType(d)


# ----------------------------------------------------------------------------------
# Categorical vocabularies (canonical values — corruption adds variants later)
# ----------------------------------------------------------------------------------
TEAMS = ("inbound_dach", "inbound_international", "partner", "enterprise")
SENIORITY = ("junior", "mid", "senior")
SOURCES = ("organic_search", "paid_search", "social", "event", "partner", "direct")
CHANNELS = ("web_form", "email", "phone", "partner_referral")
COUNTRIES = ("DE", "AT", "CH", "NL", "FR", "IT", "ES", "PL", "BE", "DK")
DACH = frozenset({"DE", "AT", "CH"})
INDUSTRIES = (
    "manufacturing",
    "retail",
    "financial_services",
    "healthcare",
    "energy",
    "automotive",
    "logistics",
    "it_services",
    "public_sector",
    "education",
)
SIZE_BANDS = ("small", "medium", "large", "enterprise")  # 1-49, 50-249, 250-999, 1000+
SIZE_BAND_EDGES = (50, 250, 1000)
EVENT_TYPES = ("call", "email", "meeting")
CAMPAIGN_SOURCES = ("paid_search", "social", "event")


@dataclass(frozen=True)
class VolumeParams:
    """How many records and over which period."""

    n_leads: int = 50_000
    start_date: str = "2025-01-01"
    n_days: int = 365
    timezone: str = "Europe/Berlin"  # business hours are local; exported timestamps are UTC
    n_agents_per_team: Mapping = field(
        default_factory=lambda: _frozen(
            {"inbound_dach": 16, "inbound_international": 10, "partner": 6, "enterprise": 8}
        )
    )
    share_agents_changing_team: float = 0.10
    campaigns_per_source: int = 8


@dataclass(frozen=True)
class MixParams:
    """Marginal and conditional distributions of lead attributes."""

    source_probs: Mapping = field(
        default_factory=lambda: _frozen(
            {
                "organic_search": 0.30,
                "paid_search": 0.22,
                "social": 0.14,
                "event": 0.10,
                "partner": 0.12,
                "direct": 0.12,
            }
        )
    )
    # channel | source (partner leads arrive almost always as referrals)
    channel_probs_partner: Mapping = field(
        default_factory=lambda: _frozen(
            {"web_form": 0.04, "email": 0.04, "phone": 0.02, "partner_referral": 0.90}
        )
    )
    channel_probs_other: Mapping = field(
        default_factory=lambda: _frozen(
            {"web_form": 0.55, "email": 0.20, "phone": 0.25, "partner_referral": 0.0}
        )
    )
    country_probs: Mapping = field(
        default_factory=lambda: _frozen(
            {
                "DE": 0.52,
                "AT": 0.12,
                "CH": 0.12,
                "NL": 0.06,
                "FR": 0.05,
                "IT": 0.04,
                "ES": 0.03,
                "PL": 0.03,
                "BE": 0.02,
                "DK": 0.01,
            }
        )
    )
    # mean of the latent lead quality z ~ N(mean, 1) by source -> lead_score = 50 + 15 z
    score_mean_by_source: Mapping = field(
        default_factory=lambda: _frozen(
            {
                "organic_search": 0.0,
                "paid_search": -0.2,
                "social": -0.5,
                "event": 0.4,
                "partner": 0.6,
                "direct": 0.2,
            }
        )
    )
    employees_log_mean: float = math.log(80)
    employees_log_sd: float = 1.4


@dataclass(frozen=True)
class ResponseParams:
    """Time to first response (minutes of *working* time after the next business opening).

    log(minutes) = channel_log_minutes[channel] + seniority[seniority]
                   + beta_score * s + beta_load * log(daily_load) + Normal(0, sigma)

    where ``s = (lead_score - 50) / 15``. Leads created outside business hours
    (Mon-Fri 08:00-18:00 local time) wait until the next opening first.
    """

    business_open_hour: int = 8
    business_close_hour: int = 18
    channel_log_minutes: Mapping = field(
        default_factory=lambda: _frozen(
            {
                "phone": math.log(12),
                "web_form": math.log(55),
                "email": math.log(110),
                "partner_referral": math.log(70),
            }
        )
    )
    seniority: Mapping = field(
        default_factory=lambda: _frozen({"junior": 0.30, "mid": 0.0, "senior": -0.25})
    )
    beta_score: float = -0.35  # agents prioritise promising leads  <-- the confounding path
    beta_load: float = 0.40  # busy days are slower
    sigma: float = 0.90
    # probability that a lead is never answered: logistic(intercept + slope * s)
    no_response_intercept: float = -3.3
    no_response_slope: float = -0.6


@dataclass(frozen=True)
class ConversionParams:
    """Probability that a lead converts into an opportunity.

    logit(p) = intercept + beta_score * s
               + beta_log2_hours * log2(1 + hours_to_first_response)   (answered leads)
               + no_response_effect                                    (never answered)
               + channel[channel] + source[source] + size_band[size_band]

    ``beta_log2_hours`` is the **causal effect of interest**: each doubling of
    (1 + hours until first response) multiplies the odds of conversion by
    ``exp(beta_log2_hours)`` = 0.85, i.e. -15 %.
    """

    intercept: float = -2.05
    beta_score: float = 0.90
    beta_log2_hours: float = math.log(0.85)
    no_response_effect: float = -2.50
    channel: Mapping = field(
        default_factory=lambda: _frozen(
            {"web_form": 0.0, "email": -0.10, "phone": 0.30, "partner_referral": 0.50}
        )
    )
    source: Mapping = field(
        default_factory=lambda: _frozen(
            {
                "organic_search": 0.0,
                "paid_search": -0.10,
                "social": -0.30,
                "event": 0.20,
                "partner": 0.40,
                "direct": 0.10,
            }
        )
    )
    size_band: Mapping = field(
        default_factory=lambda: _frozen(
            {"small": 0.0, "medium": 0.15, "large": 0.25, "enterprise": 0.35}
        )
    )
    # counterfactual policy used to compute the true business impact:
    # "every lead answered within the SLA" = response after at most this many hours
    policy_response_hours: float = 0.5


@dataclass(frozen=True)
class ActivityParams:
    """Follow-up interactions and opportunity values."""

    followups_base: float = 0.8
    followups_if_converted: float = 0.9
    followups_per_score: float = 0.3
    max_followups: int = 6
    followup_gap_days_mean: float = 2.0
    log_duration_s: Mapping = field(
        default_factory=lambda: _frozen(
            {"call": math.log(240), "email": math.log(150), "meeting": math.log(1800)}
        )
    )
    log_duration_sd: Mapping = field(
        default_factory=lambda: _frozen({"call": 0.6, "email": 0.5, "meeting": 0.3})
    )
    recording_lag_minutes_mean: float = 3.0
    opportunity_lag_days_mean: float = 5.0
    log_amount_by_size: Mapping = field(
        default_factory=lambda: _frozen(
            {
                "small": math.log(8_000),
                "medium": math.log(20_000),
                "large": math.log(45_000),
                "enterprise": math.log(110_000),
            }
        )
    )
    log_amount_sd: float = 0.6


@dataclass(frozen=True)
class CorruptionParams:
    """Rates of injected data-quality issues (see F02-T04). All rates are shares of rows."""

    exact_duplicate_leads: float = 0.02
    near_duplicate_leads: float = 0.01
    missing_industry: float = 0.08  # MCAR
    missing_company_size_web: float = 0.25  # MAR: depends on channel
    missing_company_size_other: float = 0.03
    channel_spelling_variants: float = 0.05
    country_spelling_variants: float = 0.06
    negative_response_time: float = 0.003  # clock skew on the first interaction
    extreme_response_delay: float = 0.002  # first interaction 30-60 days late
    late_arriving_interactions: float = 0.03  # recorded 2-10 days after occurring


@dataclass(frozen=True)
class GeneratorParams:
    """All parameters of one generator run."""

    volume: VolumeParams = field(default_factory=VolumeParams)
    mix: MixParams = field(default_factory=MixParams)
    response: ResponseParams = field(default_factory=ResponseParams)
    conversion: ConversionParams = field(default_factory=ConversionParams)
    activity: ActivityParams = field(default_factory=ActivityParams)
    corruption: CorruptionParams = field(default_factory=CorruptionParams)


def to_dict(obj: object) -> object:
    """JSON-friendly copy of a params dataclass (``dataclasses.asdict`` cannot copy
    the read-only ``MappingProxyType`` tables)."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: to_dict(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, Mapping):
        return {k: to_dict(v) for k, v in obj.items()}
    if isinstance(obj, tuple | list):
        return [to_dict(v) for v in obj]
    return obj
