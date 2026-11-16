"""Write a generated dataset to the landing zone (``data/raw/``).

Design rules:

* **One format per entity, on purpose:** CSV, JSON Lines and Parquet each have
  different typing pitfalls that the ingestion layer (F03) must handle.
* **Deterministic bytes:** the same seed produces byte-identical files, which the
  ``_manifest.json`` hashes make easy to verify.
* **Atomic writes:** each file is written to a temporary name and then renamed, so a
  crash never leaves a half-written file that ingestion could pick up.
* Files starting with ``_`` (manifest, ground truth) are *not* source data; the
  ingestion layer ignores them.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from lead_funnel.generator.core import GeneratedData
from lead_funnel.generator.schema import ENTITIES, Entity

logger = logging.getLogger(__name__)

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"  # ISO 8601, UTC, second precision
_ARROW_TYPES = {
    "string": pa.string(),
    "integer": pa.int64(),
    "float": pa.float64(),
    "boolean": pa.bool_(),
    "timestamp": pa.timestamp("s", tz="UTC"),
    "date": pa.date32(),
}


def _atomic_write(path: Path, write: Callable[[Path], None]) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        write(tmp)
        os.replace(tmp, path)  # atomic on the same file system
    finally:
        tmp.unlink(missing_ok=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _as_text(df: pd.DataFrame, entity: Entity) -> pd.DataFrame:
    """Format typed columns for text formats (CSV / JSON Lines)."""
    out = df.copy()
    for col in entity.columns:
        if col.type == "timestamp":
            out[col.name] = out[col.name].dt.strftime(TIMESTAMP_FORMAT)
        elif col.type == "date":
            out[col.name] = out[col.name].dt.strftime("%Y-%m-%d")
        elif col.type == "integer" and col.nullable:
            out[col.name] = out[col.name].astype("Int64")
    return out


def _write_csv(df: pd.DataFrame, entity: Entity, path: Path) -> None:
    text = _as_text(df, entity)
    _atomic_write(
        path,
        lambda p: text.to_csv(p, index=False, encoding="utf-8", lineterminator="\n"),
    )


def _write_jsonl(df: pd.DataFrame, entity: Entity, path: Path) -> None:
    text = _as_text(df, entity)
    _atomic_write(
        path,
        lambda p: text.to_json(p, orient="records", lines=True, force_ascii=False),
    )


def arrow_schema(entity: Entity) -> pa.Schema:
    return pa.schema(
        [pa.field(c.name, _ARROW_TYPES[c.type], nullable=c.nullable) for c in entity.columns]
    )


def _write_parquet(df: pd.DataFrame, entity: Entity, path: Path) -> None:
    prepared = df.copy()
    for col in entity.columns:
        if col.type == "date":
            prepared[col.name] = prepared[col.name].dt.date
    table = pa.Table.from_pandas(prepared, schema=arrow_schema(entity), preserve_index=False)
    table = table.replace_schema_metadata(None)  # drop pandas metadata: smaller, deterministic
    _atomic_write(path, lambda p: pq.write_table(table, p, compression="zstd"))


_WRITERS = {"csv": _write_csv, "jsonl": _write_jsonl, "parquet": _write_parquet}


def write_dataset(data: GeneratedData, out_dir: Path) -> dict[str, Path]:
    """Write all source files plus ground truth and a manifest. Returns name -> path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    manifest: dict[str, dict] = {}
    for name, df in data.tables.items():
        entity = ENTITIES[name]
        path = out_dir / entity.file_name
        _WRITERS[entity.format](df, entity, path)
        written[name] = path
        manifest[entity.file_name] = {"rows": len(df), "sha256": _sha256(path)}
        logger.info("Wrote %-20s %8d rows", entity.file_name, len(df))

    truth_path = out_dir / "_ground_truth.json"
    _atomic_write(
        truth_path,
        lambda p: p.write_text(
            json.dumps(data.ground_truth, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        ),
    )
    truth_leads = pa.Table.from_pandas(data.truth_leads, preserve_index=False)
    truth_leads = truth_leads.replace_schema_metadata(None)
    leads_truth_path = out_dir / "_truth_leads.parquet"
    _atomic_write(leads_truth_path, lambda p: pq.write_table(truth_leads, p, compression="zstd"))

    manifest_path = out_dir / "_manifest.json"
    _atomic_write(
        manifest_path,
        lambda p: p.write_text(
            json.dumps(
                {"seed": data.ground_truth["seed"], "files": manifest}, indent=2, sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        ),
    )
    written.update(
        {"_ground_truth": truth_path, "_truth_leads": leads_truth_path, "_manifest": manifest_path}
    )
    return written
