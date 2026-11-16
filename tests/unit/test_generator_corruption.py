"""Injected data-quality issues: present, at the configured rates, and logged."""

from __future__ import annotations

import pandas as pd

from lead_funnel.generator.core import GeneratedData
from lead_funnel.generator.params import CorruptionParams

CP = CorruptionParams()
N = 10_000  # leads in the dirty_data fixture


def _injected(data: GeneratedData) -> dict:
    return data.ground_truth["injected_issues"]


def test_clean_mode_injects_nothing(clean_data: GeneratedData) -> None:
    leads = clean_data.tables["leads"]
    assert not leads.duplicated().any()
    assert leads["industry"].notna().all()
    assert leads["company_size"].notna().all()
    assert not any(_injected(clean_data)["counts"].values())


def test_lead_issue_counts_match_configuration(dirty_data: GeneratedData) -> None:
    counts = _injected(dirty_data)["counts"]
    n_with_near = N + round(CP.near_duplicate_leads * N)
    assert counts["near_duplicate_leads"] == round(CP.near_duplicate_leads * N)
    assert counts["exact_duplicate_leads"] == round(CP.exact_duplicate_leads * n_with_near)
    assert counts["missing_industry"] == round(CP.missing_industry * n_with_near)
    assert counts["channel_spelling_variants"] == round(CP.channel_spelling_variants * n_with_near)
    assert len(dirty_data.tables["leads"]) == n_with_near + counts["exact_duplicate_leads"]


def test_exact_duplicates_are_identical_rows(dirty_data: GeneratedData) -> None:
    leads = dirty_data.tables["leads"]
    ids = _injected(dirty_data)["exact_duplicate_lead_ids"]
    assert leads.duplicated().sum() == len(ids)
    assert set(leads.loc[leads.duplicated(), "lead_id"]) == set(ids)


def test_near_duplicates_share_contact_details(dirty_data: GeneratedData) -> None:
    leads = dirty_data.tables["leads"].drop_duplicates("lead_id").set_index("lead_id")
    for original, duplicate in _injected(dirty_data)["near_duplicate_pairs"][:50]:
        a, b = leads.loc[original], leads.loc[duplicate]
        assert a["email"].lower() == b["email"].lower()
        digits = lambda s: "".join(ch for ch in s if ch.isdigit()).removeprefix("00")  # noqa: E731
        assert digits(a["phone"]) == digits(b["phone"])
        assert b["created_at"] > a["created_at"]


def test_company_size_is_missing_at_random_by_channel(dirty_data: GeneratedData) -> None:
    leads = dirty_data.tables["leads"].drop_duplicates()
    canonical_web = leads["channel"] == "web_form"  # spelling variants are excluded here
    web_rate = leads.loc[canonical_web, "company_size"].isna().mean()
    other_rate = leads.loc[~leads["channel"].str.lower().str.contains("web"), "company_size"]
    assert abs(web_rate - CP.missing_company_size_web) < 0.02
    assert other_rate.isna().mean() < 0.06


def test_spelling_variants_appear(dirty_data: GeneratedData) -> None:
    leads = dirty_data.tables["leads"]
    assert {"Web", "WEB_FORM", "Germany", "deu"} & (set(leads["channel"]) | set(leads["country"]))


def test_interaction_issues_are_detectable(dirty_data: GeneratedData) -> None:
    leads = dirty_data.tables["leads"].drop_duplicates("lead_id").set_index("lead_id")
    inter = dirty_data.tables["interactions"]
    first = inter.groupby("lead_id")["occurred_at"].min()
    hours = (first - leads["created_at"].reindex(first.index)) / pd.Timedelta(hours=1)
    log = _injected(dirty_data)

    assert set(hours.index[hours < 0]) == set(log["negative_response_lead_ids"])
    assert set(log["extreme_delay_lead_ids"]) <= set(hours.index[hours > 30 * 24])

    lag = inter["recorded_at"] - inter["occurred_at"]
    late = set(inter.loc[lag > pd.Timedelta(days=2), "interaction_id"])
    assert late == set(log["late_interaction_ids"])
