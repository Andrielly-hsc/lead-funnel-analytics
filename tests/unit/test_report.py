"""The end-to-end inference report on generated data (no warehouse needed)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from lead_funnel.analysis import inference as inf
from lead_funnel.analysis.report import run_inference, to_markdown
from lead_funnel.generator.core import generate
from tests.factories import small_params


def test_run_inference_and_markdown(tmp_path: Path) -> None:
    data = generate(small_params(20_000), seed=21, clean=True)
    leads = inf.leads_from_generated(data)
    rng = np.random.default_rng(0)
    leads = leads.assign(
        team=rng.choice(["a", "b"], len(leads)),
        n_touches=rng.integers(1, 5, len(leads)),
    )
    calls = pd.DataFrame(
        {
            "channel": rng.choice(["web_form", "email", "phone"], 3_000),
            "duration_s": rng.lognormal(5.5, 0.6, 3_000),
        }
    )
    results = run_inference(
        leads, calls, tmp_path / "figures", truth=data.ground_truth, bootstrap=10, seeds=0
    )
    assert list(results.h1["comparison"]) == [
        "all leads",
        "business hours only",
        "answered leads only",
    ]
    assert results.comparison is not None and results.seed_summary is None
    assert set(results.figures) == {"qq", "effect_comparison"}
    assert all(p.exists() for p in results.figures.values())
    text = to_markdown(results)
    for heading in (
        "## H1",
        "## H2",
        "## H3",
        "## Multiple testing",
        "## Comparison with the true",
    ):
        assert heading in text
    assert "refits (" in text and "## Bias check" not in text
