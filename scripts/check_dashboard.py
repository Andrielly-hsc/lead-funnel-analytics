"""Check the dashboard against the real warehouse (used in the CI e2e job).

    python scripts/check_dashboard.py

1. Reconciliation: the dashboard's KPIs must equal Q1 of sql/analysis/01_funnel_kpis.sql.
2. Smoke test: the Streamlit app renders every tab without an exception.
"""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

from lead_funnel.config import get_settings
from lead_funnel.dashboard.queries import reconcile_with_sql
from lead_funnel.ingestion.warehouse import connect

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with connect(get_settings().db_path, read_only=True) as con:
        table = reconcile_with_sql(con, ROOT / "sql" / "analysis" / "01_funnel_kpis.sql")
    print(table.to_string(index=False))
    if not table["match"].all():
        print("dashboard and analytical SQL disagree", file=sys.stderr)
        return 1
    at = AppTest.from_file(
        str(ROOT / "src" / "lead_funnel" / "dashboard" / "app.py"), default_timeout=120
    )
    at.run()
    if at.exception:
        print(f"app raised: {[e.value for e in at.exception]}", file=sys.stderr)
        return 1
    print(f"app ok: {len(at.metric)} KPI tiles, {len(at.tabs)} tabs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
