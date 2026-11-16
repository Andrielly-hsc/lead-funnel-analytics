"""Checks that the temporary warehouse fixture works (and serves as a usage example)."""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_tmp_warehouse_is_empty_and_writable(tmp_warehouse) -> None:
    tables = tmp_warehouse.execute("select count(*) from information_schema.tables").fetchone()
    assert tables == (0,)

    tmp_warehouse.execute("create table t as select 42 as answer")
    assert tmp_warehouse.execute("select answer from t").fetchone() == (42,)
