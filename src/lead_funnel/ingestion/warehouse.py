"""DuckDB warehouse: connection handling, schemas and the load log.

Schemas
-------
``raw``
    One table per source entity, a copy of the landing files plus load metadata
    (``_loaded_at``, ``_source_file``, ``_file_hash``, ``_run_id``).
``meta``
    Pipeline bookkeeping. ``meta.load_log`` is the audit trail of every ingestion
    decision: what was loaded, skipped or rejected, when, and why.

dbt (F04) creates the ``staging``/``marts`` schemas on top of ``raw``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb

from lead_funnel.generator.schema import Entity

DUCKDB_TYPES = {
    "string": "VARCHAR",
    "integer": "BIGINT",
    "float": "DOUBLE",
    "boolean": "BOOLEAN",
    "timestamp": "TIMESTAMPTZ",
    "date": "DATE",
}

METADATA_COLUMNS = {
    "_loaded_at": "TIMESTAMPTZ NOT NULL",
    "_source_file": "VARCHAR NOT NULL",
    "_file_hash": "VARCHAR NOT NULL",
    "_run_id": "VARCHAR NOT NULL",
}

LOAD_LOG_DDL = """
create table if not exists meta.load_log (
    run_id        varchar     not null,
    entity        varchar     not null,
    file_name     varchar     not null,
    file_hash     varchar     not null,
    status        varchar     not null
                  check (status in ('success', 'skipped', 'rejected', 'failed')),
    rows_loaded   bigint      not null default 0,
    started_at    timestamptz not null,
    finished_at   timestamptz not null,
    message       varchar
)
"""


@contextmanager
def connect(db_path: Path | str, *, read_only: bool = False) -> Iterator[duckdb.DuckDBPyConnection]:
    """Open the warehouse, always closing it (DuckDB locks the file while it is open).

    The session time zone is fixed to UTC, so ``TIMESTAMPTZ`` values are rendered the
    same way on every machine.
    """
    path = Path(db_path)
    if not read_only:
        path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path), read_only=read_only)
    try:
        con.execute("set TimeZone = 'UTC'")
        con.execute("set enable_progress_bar = false")  # keep pipeline logs clean
        yield con
    finally:
        con.close()


def ensure_schemas(con: duckdb.DuckDBPyConnection) -> None:
    """Create the ``raw`` and ``meta`` schemas and the load log (idempotent)."""
    con.execute("create schema if not exists raw")
    con.execute("create schema if not exists meta")
    con.execute(LOAD_LOG_DDL)


def raw_table_ddl(entity: Entity) -> str:
    """``CREATE TABLE`` for ``raw.<entity>``: contract columns + load metadata.

    Raw columns are nullable on purpose: the raw layer stores what the source sent;
    not-null rules are enforced by the contract check and tested again in dbt.
    """
    cols = [f"    {c.name} {DUCKDB_TYPES[c.type]}" for c in entity.columns]
    cols += [f"    {name} {ddl}" for name, ddl in METADATA_COLUMNS.items()]
    return f"create table if not exists raw.{entity.name} (\n" + ",\n".join(cols) + "\n)"


def ensure_raw_table(con: duckdb.DuckDBPyConnection, entity: Entity) -> None:
    con.execute(raw_table_ddl(entity))


def current_hash(con: duckdb.DuckDBPyConnection, entity: str) -> str | None:
    """Hash of the file whose content is currently in ``raw.<entity>``, if any."""
    row = con.execute(
        """
        select file_hash
        from meta.load_log
        where entity = ? and status = 'success'
        order by finished_at desc
        limit 1
        """,
        [entity],
    ).fetchone()
    return row[0] if row else None
