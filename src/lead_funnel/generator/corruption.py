"""Injection of realistic data-quality issues into the clean simulated tables.

Real CRM exports are never clean. This module adds the problems listed in
``CorruptionParams`` and returns an **injection log** (which rows were affected and
how). Because the log is saved with the ground truth, the data-quality feature (F05)
can measure the precision and recall of its own detection rules, which is
impossible with real data.

Counts are exact (``round(rate * n)`` rows sampled without replacement), so the
realised rates match the configuration and tests can check them precisely.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from lead_funnel.generator.params import CorruptionParams

CHANNEL_VARIANTS = {
    "web_form": ("Web", "web ", "WEB_FORM", "Web Form"),
    "email": ("E-Mail", "EMAIL", " email"),
    "phone": ("Phone", "PHONE", "telephone"),
    "partner_referral": ("Partner Referral", "partner-referral"),
}
COUNTRY_VARIANTS = {
    "DE": ("Germany", "deu", "de", "Deutschland", " DE"),
    "AT": ("Austria", "aut", "at", "Österreich"),
    "CH": ("Switzerland", "che", "ch", "Schweiz"),
    "NL": ("Netherlands", "nld", "nl"),
    "FR": ("France", "fra", "fr"),
    "IT": ("Italy", "ita", "it"),
    "ES": ("Spain", "esp", "es"),
    "PL": ("Poland", "pol", "pl"),
    "BE": ("Belgium", "bel", "be"),
    "DK": ("Denmark", "dnk", "dk"),
}


@dataclass
class InjectionLog:
    """What was corrupted, for later evaluation of data-quality rules (F05)."""

    counts: dict[str, int] = field(default_factory=dict)
    near_duplicate_pairs: list[tuple[str, str]] = field(default_factory=list)
    exact_duplicate_lead_ids: list[str] = field(default_factory=list)
    negative_response_lead_ids: list[str] = field(default_factory=list)
    extreme_delay_lead_ids: list[str] = field(default_factory=list)
    late_interaction_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "counts": self.counts,
            "near_duplicate_pairs": [list(p) for p in self.near_duplicate_pairs],
            "exact_duplicate_lead_ids": self.exact_duplicate_lead_ids,
            "negative_response_lead_ids": self.negative_response_lead_ids,
            "extreme_delay_lead_ids": self.extreme_delay_lead_ids,
            "late_interaction_ids": self.late_interaction_ids,
        }


def _sample(rng: np.random.Generator, n: int, rate: float) -> np.ndarray:
    """Exactly ``round(rate * n)`` distinct positions, sorted."""
    k = round(rate * n)
    return np.sort(rng.choice(n, size=k, replace=False)) if k else np.array([], dtype=int)


def _variant(values: pd.Series, table: dict, rng: np.random.Generator) -> list[str]:
    return [table[v][int(rng.integers(len(table[v])))] for v in values]


# ----------------------------------------------------------------------------------
# Leads
# ----------------------------------------------------------------------------------
def _near_duplicates(
    leads: pd.DataFrame, cp: CorruptionParams, rng: np.random.Generator, log: InjectionLog
) -> pd.DataFrame:
    """Same person and company registered again under a new ``lead_id``."""
    pos = _sample(rng, len(leads), cp.near_duplicate_leads)
    dup = leads.iloc[pos].copy()
    start_id = int(leads["lead_id"].str[1:].astype(int).max()) + 1
    dup["lead_id"] = [f"L{i:07d}" for i in range(start_id, start_id + len(dup))]
    dup["created_at"] = dup["created_at"] + pd.to_timedelta(
        rng.uniform(1, 7 * 24, len(dup)), unit="h"
    ).floor("s")
    # the same e-mail typed differently, the same phone in another format
    dup["email"] = np.where(rng.random(len(dup)) < 0.5, dup["email"].str.upper(), dup["email"])
    dup["phone"] = dup["phone"].str.replace("+", "00", regex=False).str.replace(" ", "-")
    dup["company_name"] = np.where(
        rng.random(len(dup)) < 0.5,
        dup["company_name"].str.lower(),
        dup["company_name"].str.split(" ").str[0],  # legal suffix dropped
    )
    dup["lead_score"] = np.clip(dup["lead_score"] + rng.integers(-5, 6, len(dup)), 0, 100)
    log.near_duplicate_pairs = list(zip(leads["lead_id"].iloc[pos], dup["lead_id"], strict=True))
    log.counts["near_duplicate_leads"] = len(dup)
    return pd.concat([leads, dup], ignore_index=True)


def corrupt_leads(
    leads: pd.DataFrame, cp: CorruptionParams, rng: np.random.Generator, log: InjectionLog
) -> pd.DataFrame:
    out = _near_duplicates(leads, cp, rng, log)
    n = len(out)

    # MCAR: industry missing completely at random
    pos = _sample(rng, n, cp.missing_industry)
    out.loc[out.index[pos], "industry"] = None
    log.counts["missing_industry"] = len(pos)

    # MAR: company size missing more often for web-form leads (optional form field)
    out["company_size"] = out["company_size"].astype("Int64")
    missing = 0
    for is_web, rate in (
        (True, cp.missing_company_size_web),
        (False, cp.missing_company_size_other),
    ):
        idx = out.index[(out["channel"] == "web_form") == is_web]
        pos = _sample(rng, len(idx), rate)
        out.loc[idx[pos], "company_size"] = pd.NA
        missing += len(pos)
    log.counts["missing_company_size"] = missing

    # inconsistent spelling of categorical codes
    pos = _sample(rng, n, cp.channel_spelling_variants)
    out.loc[out.index[pos], "channel"] = _variant(out["channel"].iloc[pos], CHANNEL_VARIANTS, rng)
    log.counts["channel_spelling_variants"] = len(pos)
    pos = _sample(rng, n, cp.country_spelling_variants)
    out.loc[out.index[pos], "country"] = _variant(out["country"].iloc[pos], COUNTRY_VARIANTS, rng)
    log.counts["country_spelling_variants"] = len(pos)

    # exact duplicates: the same row exported twice (applied last, so rows are identical)
    pos = _sample(rng, n, cp.exact_duplicate_leads)
    log.exact_duplicate_lead_ids = out["lead_id"].iloc[pos].tolist()
    log.counts["exact_duplicate_leads"] = len(pos)
    out = pd.concat([out, out.iloc[pos]], ignore_index=True)
    return out.sort_values(["created_at", "lead_id"], kind="stable", ignore_index=True)


# ----------------------------------------------------------------------------------
# Interactions
# ----------------------------------------------------------------------------------
def corrupt_interactions(
    interactions: pd.DataFrame,
    leads: pd.DataFrame,
    cp: CorruptionParams,
    rng: np.random.Generator,
    log: InjectionLog,
) -> pd.DataFrame:
    out = interactions.copy()
    first = out.sort_values("occurred_at").drop_duplicates("lead_id")
    answered = first["lead_id"].to_numpy()

    # clock skew: the first contact is stamped *before* the lead was created
    picked = answered[_sample(rng, len(answered), cp.negative_response_time)]
    created = leads.drop_duplicates("lead_id").set_index("lead_id")["created_at"]
    rows = first.index[first["lead_id"].isin(picked)]
    skew = pd.Series(pd.to_timedelta(rng.uniform(5, 120, len(rows)), unit="min"), index=rows)
    new_time = out.loc[rows, "lead_id"].map(created) - skew.dt.floor("s")
    shift = new_time - out.loc[rows, "occurred_at"]
    out.loc[rows, "occurred_at"] = new_time
    out.loc[rows, "recorded_at"] = out.loc[rows, "recorded_at"] + shift
    log.negative_response_lead_ids = sorted(picked.tolist())
    log.counts["negative_response_time"] = len(picked)

    # wrong import date: every event of a few leads is 30-60 days late
    remaining = np.setdiff1d(answered, picked)
    delayed = remaining[_sample(rng, len(remaining), cp.extreme_response_delay)]
    delay_by_lead = pd.Series(
        pd.to_timedelta(rng.uniform(30, 60, len(delayed)), unit="D").floor("s"), index=delayed
    )
    mask = out["lead_id"].isin(delayed)
    lag = out.loc[mask, "lead_id"].map(delay_by_lead)
    for col in ("occurred_at", "recorded_at"):
        out.loc[mask, col] = out.loc[mask, col] + lag
    log.extreme_delay_lead_ids = sorted(delayed.tolist())
    log.counts["extreme_response_delay"] = len(delayed)

    # late-arriving records: stored in the CRM days after they happened
    pos = _sample(rng, len(out), cp.late_arriving_interactions)
    idx = out.index[pos]
    late = pd.Series(pd.to_timedelta(rng.uniform(2, 10, len(pos)), unit="D"), index=idx)
    out.loc[idx, "recorded_at"] = out.loc[idx, "occurred_at"] + late.dt.floor("s")
    log.late_interaction_ids = out["interaction_id"].iloc[pos].tolist()
    log.counts["late_arriving_interactions"] = len(pos)

    return out
