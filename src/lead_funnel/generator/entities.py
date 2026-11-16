"""Generation of the core entities: agents, campaigns and leads.

Every function is *pure*: it receives parameters and a ``numpy.random.Generator``
and returns a new DataFrame. No file I/O, no global random state. This makes each
step deterministic for a given seed and easy to unit-test.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lead_funnel.generator import params as p
from lead_funnel.generator.params import GeneratorParams

COUNTRY_CALLING_CODES = {
    "DE": "49",
    "AT": "43",
    "CH": "41",
    "NL": "31",
    "FR": "33",
    "IT": "39",
    "ES": "34",
    "PL": "48",
    "BE": "32",
    "DK": "45",
}
LEGAL_SUFFIX = {
    "DE": ("GmbH", "AG", "GmbH & Co. KG"),
    "AT": ("GmbH", "AG"),
    "CH": ("AG", "GmbH"),
    "NL": ("B.V.", "N.V."),
    "FR": ("SAS", "SARL"),
    "IT": ("S.r.l.", "S.p.A."),
    "ES": ("S.L.", "S.A."),
    "PL": ("Sp. z o.o.",),
    "BE": ("BV", "SA"),
    "DK": ("ApS", "A/S"),
}
# fmt: off
_SYLLABLES = (
    "al", "ber", "cor", "dex", "fin", "gal", "hel", "ion", "kor", "lux",
    "mar", "nor", "ori", "pax", "qua", "ris", "sol", "tec", "ul", "ven",
    "wex", "xa", "yor", "zen", "bra", "cle", "dro", "fla", "gri", "plo",
)
# fmt: on


def size_band(employees: pd.Series | np.ndarray) -> np.ndarray:
    """Map number of employees to the company size band (small/medium/large/enterprise)."""
    idx = np.searchsorted(np.asarray(p.SIZE_BAND_EDGES), np.asarray(employees), side="right")
    return np.asarray(p.SIZE_BANDS, dtype=object)[idx]


def _choice(rng: np.random.Generator, probs: dict, size: int) -> np.ndarray:
    keys = list(probs)
    return rng.choice(np.asarray(keys, dtype=object), size=size, p=list(probs.values()))


# ----------------------------------------------------------------------------------
# Agents
# ----------------------------------------------------------------------------------
def make_agents(gp: GeneratorParams, rng: np.random.Generator) -> pd.DataFrame:
    """One row per agent version (SCD2-shaped export). A share of agents changes team once."""
    vol = gp.volume
    start = pd.Timestamp(vol.start_date)
    rows = []
    n = 0
    for team, count in vol.n_agents_per_team.items():
        for _ in range(count):
            n += 1
            rows.append(
                {
                    "agent_id": f"A{n:03d}",
                    "team": team,
                    "seniority": rng.choice(np.asarray(p.SENIORITY), p=[0.30, 0.45, 0.25]),
                    "valid_from": start - pd.Timedelta(days=int(rng.integers(30, 1500))),
                    "valid_to": pd.NaT,
                }
            )
    # a share of agents changes team once: close the old version, open a new one
    n_changes = round(len(rows) * vol.share_agents_changing_team)
    movers = rng.choice(len(rows), size=n_changes, replace=False)
    new_rows = []
    for i in sorted(movers):
        change = start + pd.Timedelta(days=int(rng.integers(60, vol.n_days - 60)))
        new_team = rng.choice(np.asarray([t for t in p.TEAMS if t != rows[i]["team"]]))
        rows[i]["valid_to"] = change
        new_rows.append({**rows[i], "team": new_team, "valid_from": change, "valid_to": pd.NaT})

    agents = pd.DataFrame(rows + new_rows)
    agents["valid_from"] = pd.to_datetime(agents["valid_from"]).dt.normalize()
    agents["valid_to"] = pd.to_datetime(agents["valid_to"]).dt.normalize()
    return agents.sort_values(["agent_id", "valid_from"], ignore_index=True)


# ----------------------------------------------------------------------------------
# Campaigns
# ----------------------------------------------------------------------------------
def make_campaigns(gp: GeneratorParams, rng: np.random.Generator) -> pd.DataFrame:
    """Sequential, non-overlapping campaigns per paid source, covering most of the period."""
    vol = gp.volume
    start = pd.Timestamp(vol.start_date)
    seg = vol.n_days / vol.campaigns_per_source
    rows = []
    n = 0
    for source in p.CAMPAIGN_SOURCES:
        for k in range(vol.campaigns_per_source):
            n += 1
            length = int(seg * rng.uniform(0.6, 0.9))
            offset = int(k * seg + rng.integers(0, max(1, int(seg) - length)))
            begin = start + pd.Timedelta(days=offset)
            rows.append(
                {
                    "campaign_id": f"C{n:03d}",
                    "campaign_name": f"{source.upper()}-{begin:%Y-%m}-{k + 1:02d}",
                    "source": source,
                    "start_date": begin,
                    "end_date": begin + pd.Timedelta(days=length - 1),
                    "budget_eur": round(float(rng.uniform(5_000, 60_000)), 2),
                }
            )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------
# Leads
# ----------------------------------------------------------------------------------
def _arrival_times(gp: GeneratorParams, rng: np.random.Generator) -> pd.DatetimeIndex:
    """Non-homogeneous arrivals: weekday/weekend, seasonality, growth trend, hour of day."""
    vol = gp.volume
    days = pd.date_range(vol.start_date, periods=vol.n_days, freq="D")
    dow = np.asarray(days.day_of_week)  # pandas 3 returns an Index; work with plain arrays
    month = np.asarray(days.month)
    weekday_factor = np.where(dow < 5, 1.0, np.where(dow == 5, 0.25, 0.15))
    seasonality = 1 + 0.15 * np.sin(2 * np.pi * (month - 3) / 12)
    trend = 1 + 0.20 * np.arange(vol.n_days) / vol.n_days
    w = weekday_factor * seasonality * trend
    day_idx = np.sort(rng.choice(vol.n_days, size=vol.n_leads, p=w / w.sum()))
    day = days[day_idx]

    # local hour of day: office-hours peak on weekdays, flatter on weekends
    hours = np.arange(24)
    weekday_profile = np.exp(-0.5 * ((hours - 12.5) / 3.2) ** 2) + 0.04
    weekend_profile = np.exp(-0.5 * ((hours - 14.0) / 5.0) ** 2) + 0.08
    is_weekend = np.asarray(day.day_of_week) >= 5
    hour = np.where(
        is_weekend,
        rng.choice(24, size=vol.n_leads, p=weekend_profile / weekend_profile.sum()),
        rng.choice(24, size=vol.n_leads, p=weekday_profile / weekday_profile.sum()),
    )
    seconds = rng.integers(0, 3600, size=vol.n_leads)
    local = day + pd.to_timedelta(hour, unit="h") + pd.to_timedelta(seconds, unit="s")
    local = local.tz_localize(
        vol.timezone, nonexistent="shift_forward", ambiguous=np.zeros(vol.n_leads, dtype=bool)
    )
    return local.tz_convert("UTC")


def _company_names(countries: np.ndarray, rng: np.random.Generator) -> list[str]:
    n = len(countries)
    s = np.asarray(_SYLLABLES)
    first = rng.choice(s, size=n)
    second = rng.choice(s, size=n)
    third = rng.choice(np.asarray(["", "", "tron", "ix", "ware", "tec", "a"]), size=n)
    suffix_pick = rng.random(n)
    names = []
    for c, a, b, t, u in zip(countries, first, second, third, suffix_pick, strict=True):
        suffixes = LEGAL_SUFFIX[c]
        suffix = suffixes[int(u * len(suffixes))]
        names.append(f"{(a + b + t).capitalize()} {suffix}")
    return names


def _contacts(
    company_names: list[str], countries: np.ndarray, rng: np.random.Generator
) -> tuple[list[str], list[str]]:
    """Fake e-mails on the reserved `.example` TLD (RFC 2606) and fake phone numbers."""
    n = len(company_names)
    letters = np.asarray(list("abcdefghijklmnopqrstuvwxyz"))
    local_parts = ["".join(x) for x in rng.choice(letters, size=(n, 7))]
    areas = rng.integers(20, 999, size=n)
    numbers = rng.integers(1_000_000, 9_999_999, size=n)
    emails, phones = [], []
    for name, c, lp, area, num in zip(
        company_names, countries, local_parts, areas, numbers, strict=True
    ):
        slug = name.split(" ")[0].lower()
        emails.append(f"{lp}@{slug}.example")
        phones.append(f"+{COUNTRY_CALLING_CODES[c]} {area} {num}")
    return emails, phones


def _assign_campaigns(
    created_local_date: pd.Series, sources: np.ndarray, campaigns: pd.DataFrame
) -> np.ndarray:
    campaign_id = np.full(len(sources), None, dtype=object)
    for row in campaigns.itertuples(index=False):
        mask = (
            (sources == row.source)
            & (created_local_date >= row.start_date).to_numpy()
            & (created_local_date <= row.end_date).to_numpy()
        )
        campaign_id[mask] = row.campaign_id
    return campaign_id


def make_leads(
    gp: GeneratorParams, rng: np.random.Generator, campaigns: pd.DataFrame
) -> pd.DataFrame:
    """Leads with their attributes. ``owner_agent_id`` is filled by :func:`assign_agents`."""
    n, mix = gp.volume.n_leads, gp.mix
    created_at = _arrival_times(gp, rng)

    source = _choice(rng, mix.source_probs, n)
    channel = np.where(
        source == "partner",
        _choice(rng, mix.channel_probs_partner, n),
        _choice(rng, mix.channel_probs_other, n),
    )
    country = _choice(rng, mix.country_probs, n)
    industry = rng.choice(np.asarray(p.INDUSTRIES, dtype=object), size=n)
    employees = np.maximum(
        1, np.round(np.exp(rng.normal(mix.employees_log_mean, mix.employees_log_sd, n)))
    ).astype("int64")
    score_mean = np.vectorize(mix.score_mean_by_source.__getitem__)(source)
    lead_score = np.clip(np.round(50 + 15 * rng.normal(score_mean, 1.0)), 0, 100).astype("int64")

    company_name = _company_names(country, rng)
    email, phone = _contacts(company_name, country, rng)

    local_date = pd.Series(created_at.tz_convert(gp.volume.timezone).tz_localize(None).normalize())
    leads = pd.DataFrame(
        {
            "lead_id": [f"L{i:07d}" for i in range(1, n + 1)],
            "created_at": created_at,
            "channel": channel,
            "source": source,
            "campaign_id": _assign_campaigns(local_date, source, campaigns),
            "country": country,
            "industry": industry,
            "company_name": company_name,
            "company_size": employees,
            "lead_score": lead_score,
            "email": email,
            "phone": phone,
            "owner_agent_id": None,
        }
    )
    return leads


def routed_team(leads: pd.DataFrame) -> np.ndarray:
    """Routing rule of the support organisation."""
    band = size_band(leads["company_size"])
    return np.select(
        [
            leads["channel"].to_numpy() == "partner_referral",
            band == "enterprise",
            leads["country"].isin(p.DACH).to_numpy(),
        ],
        ["partner", "enterprise", "inbound_dach"],
        default="inbound_international",
    )


def assign_agents(
    leads: pd.DataFrame, agents: pd.DataFrame, rng: np.random.Generator, timezone: str
) -> np.ndarray:
    """Pick, for each lead, an agent who was in the routed team on the creation date."""
    team = routed_team(leads)
    day = leads["created_at"].dt.tz_convert(timezone).dt.tz_localize(None).dt.normalize()
    far_future = pd.Timestamp("2200-01-01")  # representable in every datetime resolution
    valid_to = agents["valid_to"].fillna(far_future)
    # periods in which team membership is constant: [first day, change 1), [change 1, ...)
    boundaries = sorted({day.min()} | {d for d in agents["valid_to"].dropna() if d > day.min()})

    owner = np.full(len(leads), None, dtype=object)
    for k, lo in enumerate(boundaries):
        hi = boundaries[k + 1] if k + 1 < len(boundaries) else far_future
        in_period = ((day >= lo) & (day < hi)).to_numpy()
        active = agents[(agents["valid_from"] <= lo) & (valid_to > lo)]
        for t in p.TEAMS:
            mask = in_period & (team == t)
            candidates = active.loc[active["team"] == t, "agent_id"].to_numpy()
            if mask.any():
                owner[mask] = rng.choice(candidates, size=int(mask.sum()))
    return owner
