"""Warehouse setup: schemas, raw tables and the load log."""

from __future__ import annotations

import pytest

from lead_funnel.generator.schema import ENTITIES
from lead_funnel.ingestion import warehouse


@pytest.mark.integration
def test_connect_creates_the_file_and_always_closes(tmp_path) -> None:
    db = tmp_path / "nested" / "wh.duckdb"
    with warehouse.connect(db) as con:
        assert con.execute("select current_setting('TimeZone')").fetchone() == ("UTC",)
    assert db.exists()
    # the file is no longer locked: a second connection (read-only) can open it
    with warehouse.connect(db, read_only=True) as con:
        assert con.execute("select 1").fetchone() == (1,)


@pytest.mark.integration
def test_ensure_schemas_is_idempotent(tmp_path) -> None:
    with warehouse.connect(tmp_path / "wh.duckdb") as con:
        warehouse.ensure_schemas(con)
        warehouse.ensure_schemas(con)
        schemas = {r[0] for r in con.execute("select schema_name from duckdb_schemas()").fetchall()}
        assert {"raw", "meta"} <= schemas
        assert con.execute("select count(*) from meta.load_log").fetchone() == (0,)


@pytest.mark.integration
@pytest.mark.parametrize("name", list(ENTITIES))
def test_raw_tables_have_contract_and_metadata_columns(tmp_path, name: str) -> None:
    entity = ENTITIES[name]
    with warehouse.connect(tmp_path / "wh.duckdb") as con:
        warehouse.ensure_schemas(con)
        warehouse.ensure_raw_table(con, entity)
        cols = [
            r[0]
            for r in con.execute(
                "select column_name from information_schema.columns "
                "where table_schema = 'raw' and table_name = ? order by ordinal_position",
                [name],
            ).fetchall()
        ]
    assert cols == entity.column_names + list(warehouse.METADATA_COLUMNS)


@pytest.mark.integration
def test_load_log_rejects_unknown_status(tmp_path) -> None:
    import duckdb

    with warehouse.connect(tmp_path / "wh.duckdb") as con:
        warehouse.ensure_schemas(con)
        with pytest.raises(duckdb.ConstraintException):
            con.execute(
                "insert into meta.load_log values "
                "('r', 'leads', 'f', 'h', 'oops', 0, now(), now(), null)"
            )
