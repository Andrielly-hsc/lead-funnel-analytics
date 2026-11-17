"""Export the star schema to Parquet for BI tools (Power BI, Fabric, Tableau).

    python scripts/export_bi.py              # -> data/bi/*.parquet (git-ignored)

The same marts that feed the Streamlit dashboard: a tool-agnostic star schema is the
point of dimensional modelling. Parquet keeps types (dates, decimals, booleans) that a
CSV export would lose.
"""

from __future__ import annotations

import sys
from pathlib import Path

from lead_funnel.config import get_settings
from lead_funnel.ingestion.warehouse import connect

TABLES = (
    "fct_leads",
    "fct_interactions",
    "dim_date",
    "dim_agent",
    "dim_channel",
    "dim_lead_source",
    "dim_campaign",
)


def export(db_path: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    with connect(db_path, read_only=True) as con:
        for table in TABLES:
            path = out_dir / f"{table}.parquet"
            con.execute(f"copy marts.{table} to '{path.as_posix()}' (format parquet)")
            written.append(path)
    return written


def main() -> int:
    settings = get_settings()
    for path in export(settings.db_path, settings.data_dir / "bi"):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
