"""Small helpers that build test inputs. Import them explicitly in tests.

(Fixtures belong in ``conftest.py``; plain helper functions do not, because
importing from ``conftest`` couples tests to pytest's plugin discovery.)
"""

from __future__ import annotations

import dataclasses

from lead_funnel.generator.params import GeneratorParams


def small_params(n_leads: int) -> GeneratorParams:
    """Default parameters with a smaller number of leads."""
    gp = GeneratorParams()
    return dataclasses.replace(gp, volume=dataclasses.replace(gp.volume, n_leads=n_leads))
