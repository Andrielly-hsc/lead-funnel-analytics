"""Shared pytest fixtures.

Fixtures defined here are available to every test without importing them.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import duckdb
import pytest


@pytest.fixture
def tmp_warehouse(tmp_path: Path) -> Iterator[duckdb.DuckDBPyConnection]:
    """Yield a connection to a fresh, empty DuckDB file that is deleted after the test."""
    con = duckdb.connect(str(tmp_path / "test_warehouse.duckdb"))
    try:
        yield con
    finally:
        con.close()
