"""Matching strategies for near-duplicate leads, on a tiny hand-made example."""

from __future__ import annotations

import pandas as pd
import pytest

from lead_funnel.quality import dedup


@pytest.fixture
def leads() -> pd.DataFrame:
    t = pd.Timestamp("2025-03-01", tz="UTC")
    return pd.DataFrame(
        {
            "lead_id": ["L1", "L2", "L3", "L4", "L5"],
            "email": [
                "ana@acme.example",
                "ANA@ACME.EXAMPLE",
                "bo@acme.example",
                "cy@beta.example",
                "dee@acme.example",
            ],
            "phone": [
                "+49 30 1234567",
                "0049-30-1234567",
                "+49 30 7654321",
                "+43 1 555555",
                "+49 30 1111111",
            ],
            "company_name": ["Acme GmbH", "acme", "Acme AG", "Beta GmbH", "Acme GmbH"],
            "country_code": ["DE", "DE", "DE", "AT", "DE"],
            "created_at": [
                t,
                t + pd.Timedelta(days=2),
                t + pd.Timedelta(days=3),
                t,
                t + pd.Timedelta(days=60),
            ],
        }
    )


TRUTH = {("L1", "L2")}


def test_normalisation() -> None:
    names = pd.Series(["Flagal S.L.", "Acme GmbH & Co. KG", "Beta B.V.", "Gamma"])
    assert dedup.normalise_company(names).tolist() == ["flagal", "acme", "beta", "gamma"]
    phones = pd.Series(["+34 156 9619287", "0034-156-9619287"])
    assert dedup.normalise_phone(phones).tolist() == ["341569619287", "341569619287"]


def test_exact_email_misses_case_variants(leads: pd.DataFrame) -> None:
    assert dedup.exact_email(leads) == set()
    assert dedup.normalised_email(leads) == TRUTH
    assert dedup.normalised_phone(leads) == TRUTH
    assert dedup.email_or_phone(leads) == TRUTH


def test_pairs_are_ordered_earlier_first(leads: pd.DataFrame) -> None:
    reversed_rows = leads.iloc[::-1].reset_index(drop=True)
    assert dedup.normalised_email(reversed_rows) == {("L1", "L2")}


def test_fuzzy_company_finds_the_duplicate_but_also_false_matches(leads: pd.DataFrame) -> None:
    cand = dedup.fuzzy_company_candidates(leads, max_days=14)
    pairs = {(a, b) for a, b in zip(cand["a"], cand["b"], strict=True)}
    assert ("L1", "L2") in pairs  # found
    assert ("L1", "L3") in pairs  # different person, same company: a false match
    assert not any("L4" in p for p in pairs)  # other country: different block
    assert not any("L5" in p for p in pairs)  # 60 days later: outside the window
    assert cand["score"].between(0, 100).all()


def test_evaluate_counts_precision_and_recall() -> None:
    ev = dedup.evaluate("x", [("L2", "L1"), ("L1", "L3")], TRUTH)  # order does not matter
    assert (ev.predicted, ev.true_positives, ev.false_matches) == (2, 1, 1)
    assert (ev.precision, ev.recall) == (0.5, 1.0)
    assert ev.f1 == pytest.approx(2 / 3)
    empty = dedup.evaluate("none", [], TRUTH)
    assert (empty.precision, empty.recall, empty.f1) == (0.0, 0.0, 0.0)


def test_report(leads: pd.DataFrame) -> None:
    table = dedup.compare_strategies(leads, TRUTH, fuzzy_thresholds=(90,))
    assert len(table) == 5
    chosen = table[table["strategy"].str.contains("chosen")].iloc[0]
    assert (chosen["precision"], chosen["recall"]) == (1.0, 1.0)
    text = dedup.to_markdown(table, n_truth=1)
    assert "| normalised e-mail OR phone (chosen) | 1 | 1 | 0 | 1.000 | 1.000 | 1.000 |" in text
    assert "finds only 0% of" in text
    assert "{" not in text  # every template placeholder was filled
