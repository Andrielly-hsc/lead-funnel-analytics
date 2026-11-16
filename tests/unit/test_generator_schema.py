"""Tests for the data contract (generator.schema) and its documentation."""

from __future__ import annotations

from pathlib import Path

from lead_funnel.generator import params as p
from lead_funnel.generator.schema import ENTITIES, render_data_dictionary

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_data_dictionary_is_in_sync_with_code() -> None:
    doc = (REPO_ROOT / "docs" / "data" / "data_dictionary.md").read_text(encoding="utf-8")
    assert doc == render_data_dictionary(), (
        "docs/data/data_dictionary.md is outdated. Regenerate it with: "
        "python -m lead_funnel.generator.schema > docs/data/data_dictionary.md"
    )


def test_every_entity_declares_its_primary_key_columns() -> None:
    for entity in ENTITIES.values():
        for key in entity.primary_key.split(", "):
            assert key in entity.column_names, f"{entity.name}: PK {key} is not a column"


def test_primary_key_columns_are_not_nullable() -> None:
    for entity in ENTITIES.values():
        for col in entity.columns:
            if col.name in entity.primary_key.split(", "):
                assert not col.nullable, f"{entity.name}.{col.name} is a PK but nullable"


def test_column_names_are_snake_case_and_unique() -> None:
    for entity in ENTITIES.values():
        names = entity.column_names
        assert len(names) == len(set(names))
        assert all(n == n.lower() and " " not in n for n in names)


def test_probability_tables_sum_to_one() -> None:
    mix = p.MixParams()
    for probs in (
        mix.source_probs,
        mix.channel_probs_partner,
        mix.channel_probs_other,
        mix.country_probs,
    ):
        assert abs(sum(probs.values()) - 1.0) < 1e-9


def test_parameter_tables_cover_every_category() -> None:
    gp = p.GeneratorParams()
    assert set(gp.mix.source_probs) == set(p.SOURCES)
    assert set(gp.mix.score_mean_by_source) == set(p.SOURCES)
    assert set(gp.conversion.source) == set(p.SOURCES)
    assert set(gp.conversion.channel) == set(p.CHANNELS)
    assert set(gp.response.channel_log_minutes) == set(p.CHANNELS)
    assert set(gp.conversion.size_band) == set(p.SIZE_BANDS)
    assert set(gp.mix.country_probs) == set(p.COUNTRIES)
    assert set(gp.volume.n_agents_per_team) == set(p.TEAMS)
