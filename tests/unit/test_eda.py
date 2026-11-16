"""Descriptive statistics helpers of analysis/eda.py on small, known inputs."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lead_funnel.analysis import eda


def test_every_loaded_column_has_a_measurement_level() -> None:
    select_list = eda.LEADS_SQL.split("select", 1)[1].split("\nfrom", 1)[0]
    # each item ends with its output name: "f.lead_id" -> lead_id, "... as local_hour"
    columns = {item.strip().split()[-1].split(".")[-1] for item in select_list.split(",\n")}
    assert columns == set(eda.VARIABLES)
    levels = {v.level for v in eda.VARIABLES.values()}
    assert levels <= {"identifier", "nominal", "ordinal", "binary", "discrete", "continuous",
                      "datetime"}  # fmt: skip


def test_variable_catalog() -> None:
    df = pd.DataFrame(
        {"industry": ["retail", None, "energy", "retail"], "lead_score": [1, 2, 3, 4]}
    )
    cat = eda.variable_catalog(df).set_index("variable")
    assert cat.loc["industry", "level"] == "nominal"
    assert cat.loc["industry", "pct_missing"] == 25.0
    assert cat.loc["industry", "distinct"] == 2


def test_frequency_table_ordinal_order_and_missing_row() -> None:
    s = pd.Series(["large", "small", None, "small", "medium"], name="band")
    table = eda.frequency_table(s, order=["small", "medium", "large"])
    assert list(table.index) == ["small", "medium", "large", "(missing)"]
    assert table["n"].tolist() == [2, 1, 1, 1]
    assert table["cum_pct"].iloc[-1] == pytest.approx(1.0)


def test_frequency_table_nominal_is_sorted_by_frequency() -> None:
    s = pd.Series(["b", "a", "a", "c", "a", "b"], name="x")
    assert list(eda.frequency_table(s).index) == ["a", "b", "c"]


def test_describe_numeric_robust_and_classical() -> None:
    s = pd.Series([1, 2, 3, 4, 100, np.nan], name="v")
    d = eda.describe_numeric(s)
    assert (d["n"], d["missing"]) == (5, 1)
    assert d["median"] == 3
    assert d["mean"] == 22  # pulled up by the outlier, unlike the median
    assert d["mad"] == 1  # median of |x - 3| = [2, 1, 0, 1, 97] -> 1
    assert d["skewness"] > 2


def test_valid_response_minutes_excludes_unanswered_and_invalid() -> None:
    df = pd.DataFrame(
        {
            "is_responded": [True, True, False, True],
            "is_response_time_invalid": [False, True, False, False],
            "minutes_to_first_response": [10.0, -5.0, np.nan, 50_000.0],
        }
    )
    assert eda.valid_response_minutes(df).tolist() == [10.0, 50_000.0]  # outlier kept
