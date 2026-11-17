"""The metric layer: one definition per KPI, documentation generated from it."""

from __future__ import annotations

from pathlib import Path

import duckdb

from lead_funnel.dashboard import metrics as m

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_metrics_doc_is_in_sync_with_code() -> None:
    doc = (REPO_ROOT / "docs" / "metrics.md").read_text(encoding="utf-8")
    assert doc == m.render_metrics_doc(), (
        "docs/metrics.md is outdated: python -m lead_funnel.dashboard.metrics > docs/metrics.md"
    )


def test_keys_are_unique_and_every_metric_is_documented() -> None:
    keys = [x.key for x in m.METRICS]
    assert len(keys) == len(set(keys))
    for x in m.METRICS:
        assert (
            x.question.endswith("?") and x.caveat and x.unit in {"count", "rate", "minutes", "eur"}
        )


def test_kpi_select_runs_and_applies_the_base_filter() -> None:
    con = duckdb.connect()
    con.execute("create schema marts")
    con.execute(
        """
        create table marts.fct_leads as select * from (values
            (true,  true,  30.0, false, true,  1000.0, 3, false),
            (true,  false, 90.0, false, false, null,   1, false),
            (false, false, null, false, false, null,   0, false),
            (false, false, null, false, true,  500.0,  0, true)
        ) v(is_responded, is_sla_met, minutes_to_first_response, is_response_time_invalid,
            is_converted, opportunity_amount_eur, n_touches, is_probable_duplicate)
        """
    )
    row = con.execute(m.kpi_select()).df().iloc[0]
    assert row["leads"] == 3  # the duplicate is excluded
    assert row["conversion_rate"] == 1 / 3
    assert row["median_response_min"] == 60.0
    assert row["pipeline_eur"] == 1000.0
    assert row["pipeline_per_lead_eur"] == 1000.0 / 3
    filtered = con.execute(m.kpi_select("f.is_responded")).df().iloc[0]
    assert filtered["leads"] == 2
