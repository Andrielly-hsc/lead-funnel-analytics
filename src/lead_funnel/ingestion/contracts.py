"""Data-contract checks applied at ingestion.

Only **structural** problems are rejected here — the kind that make a file unusable
or would silently corrupt downstream tables:

* a required column is missing;
* a value cannot be cast to the contract type (raised by DuckDB while reading);
* a non-nullable column contains nulls (e.g. a missing primary key);
* the file is empty.

**Content** problems (duplicates, inconsistent spellings, outliers) are *not*
rejected: the file is loaded and they are cleaned in staging and measured in the
quality scorecard (F05). Rejecting them here would hide them from the business.

**Extra columns** are allowed with a warning (an additive schema change is
backwards compatible); they are not loaded until the contract is updated.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from lead_funnel.generator.schema import Entity

logger = logging.getLogger(__name__)


class DataContractError(Exception):
    """A landing file violates the data contract of its entity."""

    def __init__(self, entity: str, file_name: str, problems: list[str]) -> None:
        self.entity = entity
        self.file_name = file_name
        self.problems = problems
        super().__init__(f"{file_name} violates the {entity} contract: " + "; ".join(problems))


def file_columns(con: duckdb.DuckDBPyConnection, entity: Entity, path: Path) -> list[str]:
    """Column names actually present in a landing file, in file order."""
    if entity.format == "csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            return next(csv.reader(f), [])
    if entity.format == "jsonl":
        rows = con.execute(
            "select distinct unnest(json_keys(json)) as k "
            "from read_json_objects(?, format = 'newline_delimited')",
            [str(path)],
        ).fetchall()
        present = {r[0] for r in rows}
        # contract order first, then unknown keys alphabetically
        return [c for c in entity.column_names if c in present] + sorted(
            present - set(entity.column_names)
        )
    return list(pq.read_schema(path).names)


def check_columns(entity: Entity, present: list[str], file_name: str) -> None:
    """Reject missing columns; warn about extra ones."""
    missing = [c for c in entity.column_names if c not in present]
    extra = [c for c in present if c not in entity.column_names]
    if extra:
        logger.warning(
            "%s: extra columns %s are not in the %s contract and are ignored",
            file_name,
            extra,
            entity.name,
        )
    if missing:
        raise DataContractError(entity.name, file_name, [f"missing columns {missing}"])


def check_rows(con: duckdb.DuckDBPyConnection, entity: Entity, table: str, file_name: str) -> None:
    """Reject empty files and nulls in non-nullable columns of the loaded rows."""
    required = [c.name for c in entity.columns if not c.nullable]
    counts = ", ".join(f"count(*) filter (where {c} is null)" for c in required)
    row = con.execute(f"select count(*), {counts} from {table}").fetchone()
    problems = []
    if row[0] == 0:
        problems.append("file has no rows")
    problems += [
        f"{n} null value(s) in required column '{c}'"
        for c, n in zip(required, row[1:], strict=True)
        if n
    ]
    if problems:
        raise DataContractError(entity.name, file_name, problems)
