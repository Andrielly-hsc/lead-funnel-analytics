"""Fixtures for generator tests.

Generating data takes a few seconds, so datasets are built once per test session
(``scope="session"``) and shared. Tests must treat them as read-only.
"""

from __future__ import annotations

import pytest

from lead_funnel.generator.core import GeneratedData, generate
from tests.factories import small_params


@pytest.fixture(scope="session")
def clean_data() -> GeneratedData:
    """Medium-size clean dataset: large enough for statistical checks."""
    return generate(small_params(20_000), seed=123, clean=True)


@pytest.fixture(scope="session")
def dirty_data() -> GeneratedData:
    """Dataset with injected quality issues."""
    return generate(small_params(10_000), seed=123, clean=False)
