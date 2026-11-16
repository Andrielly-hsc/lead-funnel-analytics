"""Fixtures for ingestion tests.

A small landing zone is generated once per session; every test gets its own copy,
so tests can modify or break files without affecting each other.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from lead_funnel.generator.core import generate
from lead_funnel.generator.writer import write_dataset
from tests.factories import small_params


@pytest.fixture(scope="session")
def _landing_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    raw = tmp_path_factory.mktemp("template") / "raw"
    write_dataset(generate(small_params(400), seed=5), raw)
    return raw


@pytest.fixture
def landing(tmp_path: Path, _landing_template: Path) -> Path:
    """A fresh, writable copy of the landing zone: ``<tmp>/data/raw``."""
    raw = tmp_path / "data" / "raw"
    shutil.copytree(_landing_template, raw)
    return raw


@pytest.fixture
def manifest_rows(landing: Path) -> dict[str, int]:
    """Row counts per file, as declared by the generator's manifest."""
    manifest = json.loads((landing / "_manifest.json").read_text(encoding="utf-8"))
    return {name: meta["rows"] for name, meta in manifest["files"].items()}
