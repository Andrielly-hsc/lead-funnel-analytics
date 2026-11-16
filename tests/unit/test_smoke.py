"""Smoke tests: the package installs and exposes its version."""

from __future__ import annotations

import re

import lead_funnel


def test_package_exposes_semantic_version() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", lead_funnel.__version__)
