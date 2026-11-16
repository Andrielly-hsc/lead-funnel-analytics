"""Reproducibility: the same seed must give exactly the same data."""

from __future__ import annotations

import pandas as pd
import pytest

from lead_funnel.generator.core import generate
from lead_funnel.generator.writer import write_dataset
from tests.factories import small_params


def test_same_seed_gives_identical_tables() -> None:
    a = generate(small_params(1_000), seed=7)
    b = generate(small_params(1_000), seed=7)
    for name in a.tables:
        pd.testing.assert_frame_equal(a.tables[name], b.tables[name])
    assert a.ground_truth == b.ground_truth


def test_different_seeds_give_different_leads() -> None:
    a = generate(small_params(1_000), seed=7)
    b = generate(small_params(1_000), seed=8)
    assert not a.tables["leads"]["lead_score"].equals(b.tables["leads"]["lead_score"])


def test_clean_and_dirty_runs_share_the_same_simulation() -> None:
    """Corruption has its own random streams: it must not change the simulated truth."""
    clean = generate(small_params(1_000), seed=7, clean=True)
    dirty = generate(small_params(1_000), seed=7, clean=False)
    pd.testing.assert_frame_equal(clean.truth_leads, dirty.truth_leads)
    pd.testing.assert_frame_equal(clean.tables["opportunities"], dirty.tables["opportunities"])


@pytest.mark.integration
def test_written_files_are_byte_identical(tmp_path) -> None:
    data = generate(small_params(1_000), seed=7)
    first = write_dataset(data, tmp_path / "a")
    second = write_dataset(generate(small_params(1_000), seed=7), tmp_path / "b")
    for name, path in first.items():
        assert path.read_bytes() == second[name].read_bytes(), name
