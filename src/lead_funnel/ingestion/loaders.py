"""Load landing files into ``raw.<entity>``: idempotent, transactional, audited.

Load semantics
--------------
Every landing file is a **full snapshot** of its entity (that is how the CRM
exports work). Loading a file therefore *replaces* the content of its raw table,
inside one transaction, so readers see either the old or the new snapshot, never a
mix.

* **Incremental run (default):** a file is loaded only if its SHA-256 differs from
  the file whose content is currently in the raw table. Unchanged files are
  ``skipped``, so running ``ingest`` twice never duplicates data (idempotency).
* **Full refresh:** ``full_refresh=True`` reloads every file regardless of its hash.

Event-level incremental loading (appending only new rows past a watermark) is the
topic of the streaming project; it is not needed for snapshot exports.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from lead_funnel.generator.schema import ENTITIES, Entity
from lead_funnel.ingestion import warehouse
from lead_funnel.ingestion.warehouse import DUCKDB_TYPES

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoadResult:
    entity: str
    file_name: str
    status: str  # success | skipped | rejected | failed
    rows: int = 0
    message: str | None = None


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def discover(raw_dir: Path) -> list[tuple[Entity, Path]]:
    """Landing files that belong to a known entity. ``_*`` files are metadata, not data."""
    found = []
    known = {e.file_name: e for e in ENTITIES.values()}
    for path in sorted(raw_dir.iterdir()) if raw_dir.exists() else []:
        if path.name.startswith(("_", ".")) or not path.is_file():
            continue
        if path.name in known:
            found.append((known[path.name], path))
        else:
            logger.warning("Ignoring unknown landing file %s", path.name)
    for name, entity in known.items():
        if name not in {p.name for _, p in found}:
            logger.warning("Missing landing file for %s (%s)", entity.name, name)
    return found


def _columns_literal(entity: Entity) -> str:
    """DuckDB struct literal ``{'col': 'TYPE', ...}`` built from the contract."""
    return "{" + ", ".join(f"'{c.name}': '{DUCKDB_TYPES[c.type]}'" for c in entity.columns) + "}"


def select_from_file(entity: Entity) -> str:
    """SQL that reads a landing file with **explicit types** (no auto-detection).

    Auto-detection guesses types from a sample and can silently change from one file
    to the next (e.g. a column of IDs becoming integers). The contract decides.
    The file path is passed as a bound parameter (``?``), never concatenated.
    """
    cols = _columns_literal(entity)
    if entity.format == "csv":
        return (
            "select * from read_csv(?, header = true, auto_detect = false, delim = ',', "
            f"quote = '\"', escape = '\"', nullstr = '', columns = {cols})"
        )
    if entity.format == "jsonl":
        return f"select * from read_json(?, format = 'newline_delimited', columns = {cols})"
    casts = ", ".join(
        f"cast({c.name} as {DUCKDB_TYPES[c.type]}) as {c.name}" for c in entity.columns
    )
    return f"select {casts} from read_parquet(?)"


def _log(
    con: duckdb.DuckDBPyConnection,
    run_id: str,
    entity: Entity,
    path: Path,
    file_hash: str,
    result: LoadResult,
    started_at: datetime,
) -> None:
    con.execute(
        "insert into meta.load_log values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            run_id,
            entity.name,
            path.name,
            file_hash,
            result.status,
            result.rows,
            started_at,
            datetime.now(UTC),
            result.message,
        ],
    )


def load_file(
    con: duckdb.DuckDBPyConnection,
    entity: Entity,
    path: Path,
    run_id: str,
    loaded_at: datetime,
    *,
    force: bool = False,
) -> LoadResult:
    """Replace ``raw.<entity>`` with the content of ``path`` in one transaction."""
    started_at = datetime.now(UTC)
    file_hash = file_sha256(path)
    warehouse.ensure_raw_table(con, entity)

    if not force and file_hash == warehouse.current_hash(con, entity.name):
        result = LoadResult(entity.name, path.name, "skipped", message="unchanged file")
        _log(con, run_id, entity, path, file_hash, result, started_at)
        return result

    con.begin()
    try:
        con.execute(
            f"create or replace temp table _incoming as {select_from_file(entity)}", [str(path)]
        )
        con.execute(f"delete from raw.{entity.name}")
        con.execute(
            f"insert into raw.{entity.name} select *, ?, ?, ?, ? from _incoming",
            [loaded_at, path.name, file_hash, run_id],
        )
        rows = con.execute("select count(*) from _incoming").fetchone()[0]
        result = LoadResult(entity.name, path.name, "success", rows)
        _log(con, run_id, entity, path, file_hash, result, started_at)
        con.commit()
    except duckdb.Error as exc:
        con.rollback()
        result = LoadResult(entity.name, path.name, "failed", message=str(exc).splitlines()[0])
        _log(con, run_id, entity, path, file_hash, result, started_at)
        logger.error("Failed to load %s: %s", path.name, result.message)
    finally:
        con.execute("drop table if exists _incoming")
    return result


def ingest(raw_dir: Path, db_path: Path, *, full_refresh: bool = False) -> list[LoadResult]:
    """Load every landing file in ``raw_dir`` into the warehouse at ``db_path``."""
    run_id = uuid.uuid4().hex[:12]
    loaded_at = datetime.now(UTC)
    results = []
    with warehouse.connect(db_path) as con:
        warehouse.ensure_schemas(con)
        for entity, path in discover(raw_dir):
            result = load_file(con, entity, path, run_id, loaded_at, force=full_refresh)
            logger.info(
                "%-14s %-9s %8d rows  %s",
                entity.name,
                result.status,
                result.rows,
                result.message or "",
            )
            results.append(result)
    return results
