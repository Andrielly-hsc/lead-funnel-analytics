"""Quality scorecard on a minimal warehouse with known values."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from lead_funnel.quality.scorecard import METRICS, compute_scorecard, plot_scorecard, to_markdown

pytestmark = pytest.mark.integration


@pytest.fixture
def con(tmp_warehouse):
    """Tiny raw/staging/marts tables: exactly one known defect per checked rule."""
    c = tmp_warehouse
    for schema in ("raw", "staging", "marts"):
        c.execute(f"create schema {schema}")
    c.execute(
        """
        create table raw.leads as select * from (values
            ('L1', 'web_form', 'DE', 'retail', 10),
            ('L2', 'Web',      'deu', null,     null),
            ('L2', 'Web',      'deu', null,     null),
            ('L3', 'phone',    'AT', 'energy', 500)
        ) v(lead_id, channel, country, industry, company_size)
        """
    )
    c.execute(
        """
        create table raw.interactions as select * from (values
            (timestamp '2025-01-01 10:00', timestamp '2025-01-01 10:05'),
            (timestamp '2025-01-01 10:00', timestamp '2025-01-05 10:00')
        ) v(occurred_at, recorded_at)
        """
    )
    c.execute(
        """
        create table staging.stg_crm__leads as select * from (values
            ('L1', 'web_form', 'DE', 'h1', 10,   timestamp '2025-01-01'),
            ('L2', 'web_form', 'DE', 'h1', null, timestamp '2025-01-02'),
            ('L3', 'phone',    'AT', 'h3', 500,  timestamp '2025-01-03')
        ) v(lead_id, channel, country_code, email_hash, company_size, created_at)
        """
    )
    c.execute(
        """
        create table staging.stg_crm__opportunities as select * from (values
            ('L1', timestamp '2025-01-05')
        ) v(lead_id, opened_at)
        """
    )
    c.execute(
        """
        create table marts.fct_leads as select * from (values
            ('L1', true,  30.0, 'h1', false),
            ('L2', true,  -5.0, 'h1', true),
            ('L3', false, null, 'h3', false)
        ) v(lead_id, is_responded, minutes_to_first_response, email_hash, is_probable_duplicate)
        """
    )
    return c


def _row(sc: pd.DataFrame, metric: str, layer: str) -> pd.Series:
    return sc[(sc["metric"] == metric) & (sc["layer"] == layer)].iloc[0]


def test_values_and_statuses(con) -> None:
    sc = compute_scorecard(con, truth_path=None)
    assert len(sc) == len(METRICS)
    raw_unique = _row(sc, "lead rows unique by lead_id", "raw")
    assert (raw_unique["conforming"], raw_unique["total"], raw_unique["status"]) == (3, 4, "FAIL")
    assert _row(sc, "lead rows unique by lead_id", "staging")["status"] == "PASS"
    assert _row(sc, "channel is a canonical code", "raw")["value"] == 0.5
    assert _row(sc, "one lead per person (e-mail)", "staging")["conforming"] == 2
    deduplicated = _row(sc, "one lead per person, flagged duplicates excluded", "marts")
    assert (deduplicated["conforming"], deduplicated["total"]) == (2, 2)
    assert _row(sc, "response time not negative", "marts")["value"] == 0.5
    assert _row(sc, "interaction recorded within 48 h", "raw")["status"] == "FAIL"


def test_accuracy_is_not_available_without_truth(con) -> None:
    sc = compute_scorecard(con, truth_path=Path("does-not-exist.parquet"))
    assert set(sc.loc[sc["dimension"] == "accuracy", "status"]) == {"n/a"}


def test_accuracy_with_truth(con, tmp_path: Path) -> None:
    truth = tmp_path / "truth.parquet"
    pd.DataFrame(
        {
            "lead_id": ["L1", "L2", "L3"],
            "true_hours_to_first_response": [0.5, 0.25, None],
            "true_company_size": [10, 77, 500],
        }
    ).to_parquet(truth)
    sc = compute_scorecard(con, truth_path=truth)
    response = _row(sc, "response time matches the truth (±1 min)", "marts")
    assert (response["conforming"], response["total"]) == (1, 2)  # L2 is skewed
    assert _row(sc, "company size matches the truth", "staging")["value"] == 1.0


def test_markdown_and_figure(con, tmp_path: Path) -> None:
    sc = compute_scorecard(con, truth_path=None)
    text = to_markdown(sc, figure="fig.png")
    assert "![Data-quality scorecard](fig.png)" in text
    assert "❌ FAIL" in text and "➖ n/a" in text
    assert "- **timeliness:** 0/1" in text
    path = plot_scorecard(sc, tmp_path / "figs" / "scorecard.png")
    assert path.exists() and path.stat().st_size > 10_000
