"""Column profiling on a small table with known values."""

from __future__ import annotations

from pathlib import Path

import pytest

from lead_funnel import cli
from lead_funnel.quality.profiling import profile_table, to_markdown, write_profiles

pytestmark = pytest.mark.integration


@pytest.fixture
def con(tmp_warehouse):
    tmp_warehouse.execute("create schema raw")
    tmp_warehouse.execute(
        """
        create table raw.t as
        select * from (values
            ('a', 10, 'x', now()),
            ('b', 20, null, now()),
            ('b', 20, null, now()),
            ('c', null, 'x', now())
        ) v(id, amount, code, _loaded_at)
        """
    )
    return tmp_warehouse


def test_profile_counts_are_exact(con) -> None:
    p = profile_table(con, "raw.t")
    assert (p.rows, p.duplicate_rows) == (4, 1)
    cols = p.columns.set_index("column")
    assert list(cols.index) == ["id", "amount", "code"]  # metadata column excluded
    assert cols.loc["id", "distinct"] == 3
    assert cols.loc["code", "pct_null"] == 50.0
    assert cols.loc["amount", "mean"] == pytest.approx(16.667, abs=1e-3)
    assert cols.loc["amount", "median"] == 20
    assert cols.loc["code", "top_values"] == "`x` (2)"
    assert cols.loc["amount", "top_values"] == ""  # only text columns get top values


def test_markdown_report(con) -> None:
    text = to_markdown(profile_table(con, "raw.t"))
    assert "**Fully duplicated rows:** 1" in text
    assert "| `code` | VARCHAR | 50.0 |" in text
    assert "_loaded_at" not in text


def test_unknown_table_raises(con) -> None:
    with pytest.raises(ValueError, match="not found"):
        profile_table(con, "raw.missing")


def test_write_profiles_creates_one_file_per_table(con, tmp_path: Path) -> None:
    paths = write_profiles(con, ["raw.t"], tmp_path / "out")
    assert [p.name for p in paths] == ["profile_t.md"]
    assert paths[0].read_text(encoding="utf-8").startswith("# Profile")


def test_cli_profile_needs_a_warehouse(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LF_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("LF_DB_PATH", raising=False)
    assert cli.main(["profile"]) == 2


def test_cli_profile_without_dbt_models_explains_what_to_run(
    landing: Path, monkeypatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Raw tables exist (ingested) but dbt has not built staging/marts yet."""
    import logging

    from lead_funnel.ingestion.loaders import ingest

    data_dir = landing.parent
    db = data_dir / "warehouse" / "lead_funnel.duckdb"
    ingest(landing, db)
    monkeypatch.chdir(data_dir.parent)
    monkeypatch.setenv("LF_DATA_DIR", str(data_dir))
    monkeypatch.setenv("LF_REPORTS_DIR", str(data_dir.parent / "reports"))
    monkeypatch.delenv("LF_DB_PATH", raising=False)
    with caplog.at_level(logging.ERROR):
        assert cli.main(["profile"]) == 2
    assert "Run `dbt build`" in caplog.text
    assert (data_dir.parent / "reports" / "quality" / "profile_leads.md").exists()
