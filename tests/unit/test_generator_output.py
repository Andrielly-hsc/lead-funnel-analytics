"""The generated tables honour the data contract (schema.py)."""

from __future__ import annotations

import pandas as pd
import pytest
from pandas.api import types as pdt

from lead_funnel.generator.core import GeneratedData
from lead_funnel.generator.schema import ENTITIES

TYPE_CHECKS = {
    "string": pdt.is_string_dtype,
    "integer": pdt.is_integer_dtype,
    "float": pdt.is_float_dtype,
    "boolean": pdt.is_bool_dtype,
    "timestamp": lambda s: isinstance(s.dtype, pd.DatetimeTZDtype) and str(s.dt.tz) == "UTC",
    "date": pdt.is_datetime64_dtype,
}


@pytest.mark.parametrize("name", list(ENTITIES))
def test_columns_and_types_match_the_contract(clean_data: GeneratedData, name: str) -> None:
    df, entity = clean_data.tables[name], ENTITIES[name]
    assert list(df.columns) == entity.column_names
    for col in entity.columns:
        assert TYPE_CHECKS[col.type](df[col.name]), f"{name}.{col.name}: {df[col.name].dtype}"
        if not col.nullable:
            assert df[col.name].notna().all(), f"{name}.{col.name} has nulls"


@pytest.mark.parametrize("name", list(ENTITIES))
def test_clean_data_uses_only_canonical_values(clean_data: GeneratedData, name: str) -> None:
    df, entity = clean_data.tables[name], ENTITIES[name]
    for col in entity.columns:
        if col.allowed:
            assert set(df[col.name].dropna()) <= set(col.allowed), f"{name}.{col.name}"


def test_primary_keys_are_unique_in_clean_data(clean_data: GeneratedData) -> None:
    t = clean_data.tables
    assert t["leads"]["lead_id"].is_unique
    assert t["interactions"]["interaction_id"].is_unique
    assert t["opportunities"]["opportunity_id"].is_unique
    assert t["campaigns"]["campaign_id"].is_unique
    assert not t["agents"].duplicated(["agent_id", "valid_from"]).any()


def test_foreign_keys_resolve(clean_data: GeneratedData) -> None:
    t = clean_data.tables
    lead_ids = set(t["leads"]["lead_id"])
    agent_ids = set(t["agents"]["agent_id"])
    assert set(t["interactions"]["lead_id"]) <= lead_ids
    assert set(t["opportunities"]["lead_id"]) <= lead_ids
    assert set(t["interactions"]["agent_id"]) <= agent_ids
    assert set(t["leads"]["owner_agent_id"]) <= agent_ids
    assert set(t["leads"]["campaign_id"].dropna()) <= set(t["campaigns"]["campaign_id"])


def test_value_ranges(clean_data: GeneratedData) -> None:
    t = clean_data.tables
    assert t["leads"]["lead_score"].between(0, 100).all()
    assert (t["leads"]["company_size"] >= 1).all()
    assert (t["interactions"]["duration_s"] > 0).all()
    assert (t["interactions"]["recorded_at"] >= t["interactions"]["occurred_at"]).all()
    assert (t["opportunities"]["amount_eur"] > 0).all()
    assert t["leads"]["email"].str.endswith(".example").all()  # reserved TLD, never real


def test_agent_history_is_consistent(clean_data: GeneratedData) -> None:
    agents = clean_data.tables["agents"].sort_values(["agent_id", "valid_from"])
    # exactly one current version per agent
    assert (agents.groupby("agent_id")["valid_to"].apply(lambda s: s.isna().sum()) == 1).all()
    # versions are contiguous: valid_to of one == valid_from of the next
    nxt = agents.groupby("agent_id")["valid_from"].shift(-1)
    closed = agents["valid_to"].notna()
    assert (agents.loc[closed, "valid_to"] == nxt[closed]).all()
    assert agents["agent_id"].nunique() < len(agents)  # some agents changed team
