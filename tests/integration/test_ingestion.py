"""End-to-end ingestion: landing files -> raw layer, with idempotency and failure handling."""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from lead_funnel import cli
from lead_funnel.generator.schema import ENTITIES
from lead_funnel.ingestion import contracts, loaders, warehouse

pytestmark = pytest.mark.integration


def _ingest(landing: Path, **kwargs) -> dict[str, loaders.LoadResult]:
    results = loaders.ingest(landing, landing.parent / "wh.duckdb", **kwargs)
    return {r.entity: r for r in results}


def _query(landing: Path, sql: str, params: list | None = None) -> list[tuple]:
    with warehouse.connect(landing.parent / "wh.duckdb", read_only=True) as con:
        return con.execute(sql, params or []).fetchall()


def _count(landing: Path, table: str) -> int:
    return _query(landing, f"select count(*) from {table}")[0][0]


# ----------------------------------------------------------------------------------
# Happy path and reconciliation
# ----------------------------------------------------------------------------------
def test_all_files_load_and_row_counts_reconcile(landing: Path, manifest_rows) -> None:
    results = _ingest(landing)
    assert {r.status for r in results.values()} == {"success"}
    for name, entity in ENTITIES.items():
        assert results[name].rows == manifest_rows[entity.file_name]
        assert _count(landing, f"raw.{name}") == manifest_rows[entity.file_name]


def test_metadata_columns_are_filled(landing: Path) -> None:
    _ingest(landing)
    rows = _query(
        landing,
        "select count(distinct _run_id), count(distinct _file_hash), "
        "count(*) filter (where _loaded_at is null), min(_source_file) from raw.leads",
    )
    assert rows == [(1, 1, 0, "leads.csv")]


def test_types_follow_the_contract(landing: Path) -> None:
    _ingest(landing)
    types = dict(
        _query(
            landing,
            "select column_name, data_type from information_schema.columns "
            "where table_schema = 'raw' and table_name = 'interactions'",
        )
    )
    assert types["occurred_at"] == "TIMESTAMP WITH TIME ZONE"
    assert types["duration_s"] == "BIGINT"
    assert _query(landing, "select typeof(valid_from) from raw.agents limit 1") == [("DATE",)]


def test_metadata_files_are_not_loaded(landing: Path) -> None:
    found = {p.name for _, p in loaders.discover(landing)}
    assert found == {e.file_name for e in ENTITIES.values()}
    assert not any(name.startswith("_") for name in found)


def test_unknown_and_missing_files_are_reported(
    landing: Path, caplog: pytest.LogCaptureFixture
) -> None:
    (landing / "notes.txt").write_text("hello", encoding="utf-8")
    (landing / "agents.parquet").unlink()
    with caplog.at_level(logging.WARNING):
        found = loaders.discover(landing)
    assert "agents" not in {e.name for e, _ in found}
    assert "Ignoring unknown landing file notes.txt" in caplog.text
    assert "Missing landing file for agents" in caplog.text


# ----------------------------------------------------------------------------------
# Idempotency
# ----------------------------------------------------------------------------------
def test_second_run_skips_everything_and_duplicates_nothing(landing: Path) -> None:
    _ingest(landing)
    before = _count(landing, "raw.interactions")
    second = _ingest(landing)
    assert {r.status for r in second.values()} == {"skipped"}
    assert _count(landing, "raw.interactions") == before
    statuses = _query(landing, "select status, count(*) from meta.load_log group by 1 order by 1")
    assert statuses == [("skipped", 5), ("success", 5)]


def test_changed_file_replaces_its_snapshot_only(landing: Path) -> None:
    _ingest(landing)
    leads = pd.read_csv(landing / "leads.csv", dtype=str, keep_default_na=False)
    leads.head(100).to_csv(landing / "leads.csv", index=False)  # a smaller new snapshot

    results = _ingest(landing)
    assert results["leads"].status == "success"
    assert {r.status for n, r in results.items() if n != "leads"} == {"skipped"}
    assert _count(landing, "raw.leads") == 100  # replaced, not appended


def test_full_refresh_reloads_every_file(landing: Path, manifest_rows) -> None:
    _ingest(landing)
    results = _ingest(landing, full_refresh=True)
    assert {r.status for r in results.values()} == {"success"}
    assert _count(landing, "raw.leads") == manifest_rows["leads.csv"]
    assert _query(landing, "select count(distinct _run_id) from raw.leads") == [(1,)]


# ----------------------------------------------------------------------------------
# Contract violations
# ----------------------------------------------------------------------------------
def _drop_csv_column(path: Path, column: str) -> None:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.drop(columns=column).to_csv(path, index=False)


def _null_parquet_key(path: Path, column: str) -> None:
    table = pq.read_table(path)
    values = table.column(column).to_pylist()
    values[0] = None
    idx = table.schema.get_field_index(column)
    pq.write_table(table.set_column(idx, pa.field(column, pa.string()), pa.array(values)), path)


def _bad_json_value(path: Path, _: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(
            '{"interaction_id": "IX", "lead_id": "L1", "agent_id": "A1", "event_type": "call", '
            '"occurred_at": "yesterday", "recorded_at": "2025-01-01T00:00:00Z", "duration_s": 3}\n'
        )


def _empty_csv(path: Path, _: str) -> None:
    header = path.read_text(encoding="utf-8").splitlines()[0]
    path.write_text(header + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("entity", "breaker", "column", "message"),
    [
        ("opportunities", _drop_csv_column, "amount_eur", "missing columns ['amount_eur']"),
        ("campaigns", _null_parquet_key, "campaign_id", "null value(s) in required column"),
        ("interactions", _bad_json_value, "", "invalid timestamp"),
        ("leads", _empty_csv, "", "file has no rows"),
    ],
)
def test_contract_violations_are_rejected_and_quarantined(
    landing: Path, entity: str, breaker, column: str, message: str
) -> None:
    path = landing / ENTITIES[entity].file_name
    breaker(path, column)

    result = _ingest(landing)[entity]
    assert result.status == "rejected"
    assert message in result.message
    assert not path.exists()
    quarantined = list((landing.parent / "quarantine").iterdir())
    assert [p.name.split("__", 1)[1] for p in quarantined] == [path.name]
    assert _count(landing, f"raw.{entity}") == 0
    logged = _query(landing, "select status from meta.load_log where entity = ?", [entity])
    assert logged == [("rejected",)]


def test_rejected_file_keeps_the_previous_snapshot(landing: Path, manifest_rows) -> None:
    _ingest(landing)
    _drop_csv_column(landing / "leads.csv", "email")
    assert _ingest(landing)["leads"].status == "rejected"
    assert _count(landing, "raw.leads") == manifest_rows["leads.csv"]  # rollback kept old data


def test_extra_and_reordered_columns_are_accepted(
    landing: Path, manifest_rows, caplog: pytest.LogCaptureFixture
) -> None:
    path = landing / "leads.csv"
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df[list(reversed(df.columns))].assign(utm_medium="cpc").to_csv(path, index=False)

    with caplog.at_level(logging.WARNING):
        result = _ingest(landing)["leads"]
    assert result.status == "success"
    assert "extra columns ['utm_medium']" in caplog.text
    cols = [r[0] for r in _query(landing, "select column_name from (describe raw.leads)")]
    assert "utm_medium" not in cols
    assert _query(landing, "select count(*) from raw.leads where lead_id like 'L%'") == [
        (manifest_rows["leads.csv"],)
    ]


def test_database_error_fails_without_quarantine_and_rolls_back(
    landing: Path, monkeypatch: pytest.MonkeyPatch, manifest_rows
) -> None:
    _ingest(landing)
    leads = pd.read_csv(landing / "leads.csv", dtype=str, keep_default_na=False)
    leads.head(10).to_csv(landing / "leads.csv", index=False)

    def boom(*args, **kwargs):
        raise duckdb.IOException("disk full (simulated)")

    monkeypatch.setattr(contracts, "check_rows", boom)
    result = _ingest(landing)["leads"]
    assert result.status == "failed"
    assert "disk full" in result.message
    assert (landing / "leads.csv").exists()  # left in place for a retry
    assert _count(landing, "raw.leads") == manifest_rows["leads.csv"]


# ----------------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------------
@pytest.fixture
def cli_env(landing: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(landing.parent.parent)
    for var in ("LF_SEED", "LF_SLA_MINUTES", "LF_DB_PATH", "LF_LOG_LEVEL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("LF_DATA_DIR", str(landing.parent))
    return landing


def test_cli_ingest_exit_codes(cli_env: Path) -> None:
    assert cli.main(["ingest"]) == 0
    assert cli.main(["ingest"]) == 0  # all skipped is still a success
    _drop_csv_column(cli_env / "leads.csv", "email")
    assert cli.main(["ingest"]) == 1  # a rejected file makes the run fail
    assert (cli_env.parent / "quarantine").is_dir()


def test_cli_ingest_without_landing_folder(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LF_DATA_DIR", str(tmp_path / "nothing"))
    assert cli.main(["ingest"]) == 2
