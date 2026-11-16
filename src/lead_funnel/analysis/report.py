"""Run the whole pre-registered inference and publish it (``lead-funnel report``).

One function, :func:`run_inference`, executes every analysis of reports/analysis_plan.md in
order and returns plain tables; :func:`to_markdown` renders them. The CLI and the notebook
``02_inference.ipynb`` both call these, so the published numbers and the notebook can never
disagree.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from lead_funnel.analysis import inference as inf
from lead_funnel.analysis import regression as reg
from lead_funnel.analysis import robustness as rob

logger = logging.getLogger(__name__)


@dataclass
class InferenceResults:
    h1: pd.DataFrame
    correlations: pd.DataFrame
    anova: pd.DataFrame
    coefficients: pd.DataFrame
    binned: pd.DataFrame
    stratified: pd.DataFrame
    calibration: pd.DataFrame
    segments: pd.DataFrame
    sensitivity: pd.DataFrame
    comparison: pd.DataFrame | None = None
    seed_summary: pd.DataFrame | None = None
    figures: dict[str, Path] = field(default_factory=dict)


def run_inference(
    leads: pd.DataFrame,
    calls: pd.DataFrame,
    figures_dir: Path,
    *,
    truth: dict | None = None,
    bootstrap: int = 200,
    seeds: int = 20,
) -> InferenceResults:
    """Every pre-registered analysis, in the plan's order. ``truth`` is only used at the end."""
    df = inf.analysis_frame(leads)

    # H1 — proportions
    h1 = inf.proportion_test_table(
        {
            "all leads": inf.sla_conversion_test(df),
            "business hours only": inf.sla_conversion_test(df[df["business_hours"]]),
            "answered leads only": inf.sla_conversion_test(df[df["is_responded"]]),
        }
    )

    # correlations and H2 — ANOVA
    answered = df[df["is_responded"]]
    correlations = inf.correlation_table(answered, ["lead_score", "hours", "n_touches"])
    anova = inf.anova_summary(
        {
            "H2a log10(response hours) ~ channel": inf.one_way_anova(
                np.log10(answered["hours"].clip(lower=1 / 60)), answered["channel"]
            ),
            "H2b call duration ~ channel": inf.one_way_anova(calls["duration_s"], calls["channel"]),
        }
    )
    figures = {
        "qq": inf.plot_qq(
            answered["hours"],
            answered["channel"],
            figures_dir / "inference_qq.png",
            title="Response time: residuals are far from normal on the raw scale, "
            "much closer on the log scale",
        )
    }

    # H3 — naïve vs adjusted models
    naive = reg.fit(reg.NAIVE_HOURS, df)
    adjusted = reg.fit(reg.ADJUSTED, df)
    coefficients = pd.DataFrame(
        [
            {"model": name, **vars(reg.coefficient(m, "log2_hours"))}
            for name, m in (("naïve", naive), ("adjusted", adjusted))
        ]
    )
    coefficients["odds_ratio"] = np.exp(coefficients["estimate"])
    ame = reg.average_marginal_effect(adjusted, "log2_hours")
    coefficients["ame_pp"] = [np.nan, ame[0]]

    # robustness
    segments = rob.segment_tests(df)
    sensitivity = rob.sensitivity_table(leads)

    results = InferenceResults(
        h1=h1,
        correlations=correlations,
        anova=anova,
        coefficients=coefficients,
        binned=reg.binned_model_table(df),
        stratified=reg.stratified_gap(df),
        calibration=reg.calibration_table(adjusted, df),
        segments=segments,
        sensitivity=sensitivity,
        figures=figures,
    )

    if truth is not None:  # comparison with the generator's truth — always last
        boot = reg.bootstrap_policy(df, resamples=bootstrap)
        h1_all = inf.sla_conversion_test(df)
        results.comparison = reg.compare_with_truth(
            (100 * h1_all.diff, 100 * h1_all.diff_ci[0], 100 * h1_all.diff_ci[1]),
            reg.coefficient(naive, "log2_hours"),
            reg.coefficient(adjusted, "log2_hours"),
            reg.g_computation(adjusted, df),
            boot,
            truth,
        )
        results.comparison.attrs.update(
            bootstrap_failed=boot.attrs["failed"], bootstrap_resamples=boot.attrs["resamples"]
        )
        figures["effect_comparison"] = reg.plot_effect_comparison(
            results.comparison, figures_dir / "inference_effect_comparison.png"
        )
        if seeds:
            study = rob.seed_study(range(1, seeds + 1))
            results.seed_summary = rob.seed_study_summary(study)
            c = reg.coefficient(adjusted, "log2_hours")
            figures["seed_study"] = rob.plot_seed_study(
                study,
                figures_dir / "inference_seed_study.png",
                highlight=("this warehouse", c.estimate, *c.ci),
            )
    return results


def _table(df: pd.DataFrame, digits: int = 4) -> str:
    def fmt(v: object) -> str:
        if isinstance(v, float):
            if np.isnan(v):
                return "∅"
            return f"{v:.2e}" if 0 < abs(v) < 1e-4 else f"{v:,.{digits}f}"
        return str(v)

    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    rows = ["| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join([head, sep, *rows])


def to_markdown(r: InferenceResults) -> str:
    """All results as one Markdown document (figures linked relative to reports/inference/)."""
    s = r.stratified.attrs
    parts = [
        "# Inference results",
        "",
        "> Generated by `lead-funnel report` following the pre-registered "
        "[analysis plan](../analysis_plan.md). Interpretation: "
        "[analysis report](../analysis_report.md).",
        "",
        "## H1 — conversion, SLA met vs missed (naïve association)",
        "",
        _table(r.h1),
        "",
        "## Correlations (answered leads)",
        "",
        _table(r.correlations),
        "",
        "## H2 — one-way ANOVA with assumption checks",
        "",
        _table(r.anova),
        "",
        f"![Q-Q plots](../figures/{r.figures['qq'].name})",
        "",
        "## H3 — response time and conversion: naïve vs adjusted logistic model",
        "",
        _table(r.coefficients.drop(columns=["term", "ci"])),
        "",
        "Functional-form check (adjusted odds ratios by response-time band):",
        "",
        _table(r.binned, 3),
        "",
        f"Stratifying by lead-score quintile alone shrinks the gap from "
        f"{s['crude_gap_pp']:.1f} pp (crude) to {s['stratified_gap_pp']:.1f} pp:",
        "",
        _table(r.stratified),
        "",
        "Calibration of the adjusted model (deciles of predicted probability):",
        "",
        _table(r.calibration.reset_index()),
        "",
        "## Multiple testing — H1 within 19 segments",
        "",
        _table(r.segments),
        "",
        "## Sensitivity of the adjusted analysis",
        "",
        _table(r.sensitivity, 3),
    ]
    if r.comparison is not None:
        parts += [
            "",
            "## Comparison with the true effects (synthetic data only)",
            "",
            _table(r.comparison.drop(columns=["quantity"])),
            "",
            "Percentage-point CIs: percentile bootstrap, "
            f"{r.comparison.attrs['bootstrap_resamples']} refits "
            f"({r.comparison.attrs['bootstrap_failed']} skipped for non-convergence).",
            "",
            f"![naïve vs adjusted vs truth](../figures/{r.figures['effect_comparison'].name})",
        ]
    if r.seed_summary is not None:
        a = r.seed_summary.attrs
        parts += [
            "",
            f"## Bias check on {a['seeds']} independent datasets",
            "",
            _table(r.seed_summary),
            "",
            f"Coverage of the 95 % CI for β: **{a['beta_coverage']:.0%}**.",
            "",
            f"![seed study](../figures/{r.figures['seed_study'].name})",
        ]
    return "\n".join(parts) + "\n"
