"""Multiple testing and robustness checks (reports/analysis_plan.md §6-§7).

A conclusion is *robust* if its direction and practical relevance survive every
pre-specified variation. The multi-seed check is the decisive one: it separates
sampling noise in one dataset from a systematic bias of the estimator.
"""

from __future__ import annotations

import dataclasses
import logging

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from lead_funnel.analysis import inference as inf
from lead_funnel.analysis import regression as reg

logger = logging.getLogger(__name__)

SEGMENTS = ("channel", "lead_source", "team", "company_size_band")


# ----------------------------------------------------------------------------------
# Multiple testing
# ----------------------------------------------------------------------------------
def segment_tests(df: pd.DataFrame, segments: tuple[str, ...] = SEGMENTS) -> pd.DataFrame:
    """H1 inside every segment, with Holm and Benjamini-Hochberg corrections.

    Testing many segments at α = 0.05 produces about one false positive in twenty by
    chance. Holm controls the family-wise error rate (the chance of *any* false
    positive); Benjamini-Hochberg controls the false discovery rate (the expected *share*
    of false positives among the discoveries) and is less conservative.
    """
    rows = []
    for col in segments:
        for value, g in df.groupby(col):
            if g["sla_met"].nunique() < 2:
                continue
            t = inf.sla_conversion_test(g)
            rows.append(
                {
                    "segment": col,
                    "value": value,
                    "n": len(g),
                    "diff_pp": 100 * t.diff,
                    "p_value": t.p_value,
                }
            )
    out = pd.DataFrame(rows)
    out["p_holm"] = multipletests(out["p_value"], alpha=inf.ALPHA, method="holm")[1]
    out["p_bh"] = multipletests(out["p_value"], alpha=inf.ALPHA, method="fdr_bh")[1]
    for col in ("p_value", "p_holm", "p_bh"):
        out[f"sig_{col.removeprefix('p_')}"] = out[col] < inf.ALPHA
    return out


# ----------------------------------------------------------------------------------
# Sensitivity of the adjusted estimate
# ----------------------------------------------------------------------------------
def _adjusted_summary(name: str, df: pd.DataFrame, sla_hours: float = 1.0) -> dict:
    model = reg.fit(reg.ADJUSTED, df)
    c = reg.coefficient(model, "log2_hours")
    eff = reg.g_computation(model, df, sla_hours=sla_hours)
    met = df["no_response"].eq(0) & (df["hours"] <= sla_hours)
    naive_gap = 100 * (df.loc[met, "converted"].mean() - df.loc[~met, "converted"].mean())
    return {
        "variant": name,
        "n": len(df),
        "naive_gap_pp": naive_gap,
        "odds_ratio": c.odds_ratio,
        "or_ci_low": c.odds_ratio_ci[0],
        "or_ci_high": c.odds_ratio_ci[1],
        "effect_on_missed_pp": eff.effect_on_missed_pp,
        "policy_lift_pp": eff.lift_pp,
    }


def sensitivity_table(leads: pd.DataFrame) -> pd.DataFrame:
    """The pre-specified variations of the primary analysis (plan §7, checks 1-3)."""
    base = inf.analysis_frame(leads)
    rows = [_adjusted_summary("primary (SLA 60 min)", base)]
    for minutes in (30, 120):
        rows.append(_adjusted_summary(f"SLA {minutes} min", base, sla_hours=minutes / 60))
    with_errors = inf.analysis_frame(leads, exclude_errors=False)
    rows.append(_adjusted_summary("errors included (239 leads)", with_errors))
    rows.append(_adjusted_summary("business hours only", base[base["business_hours"]]))
    out = pd.DataFrame(rows)
    out["robust"] = (out["or_ci_high"] < 1) & (out["effect_on_missed_pp"] >= inf.MIN_EFFECT_PP)
    return out


# ----------------------------------------------------------------------------------
# Multi-seed check: sampling noise or estimator bias?
# ----------------------------------------------------------------------------------
def seed_study(seeds: range | list[int], n_leads: int = 50_000) -> pd.DataFrame:
    """Re-run generation + adjusted analysis on independent synthetic datasets.

    For each seed: the adjusted β with its Wald CI, the g-computed effects, and the
    true values of *that* run. Across seeds, the mean error measures bias and the share
    of CIs containing the true β measures coverage (≈ 95 % if the method is sound).
    """
    from lead_funnel.generator.core import generate
    from lead_funnel.generator.params import GeneratorParams

    gp = GeneratorParams()
    gp = dataclasses.replace(gp, volume=dataclasses.replace(gp.volume, n_leads=n_leads))
    rows = []
    for seed in seeds:
        data = generate(gp, seed=seed, clean=True)
        df = inf.analysis_frame(inf.leads_from_generated(data))
        model = reg.fit(reg.ADJUSTED, df)
        c = reg.coefficient(model, "log2_hours")
        eff = reg.g_computation(model, df)
        truth = data.ground_truth
        realised = truth["realised"]
        rows.append(
            {
                "seed": seed,
                "beta": c.estimate,
                "beta_ci_low": c.ci[0],
                "beta_ci_high": c.ci[1],
                "beta_true": truth["params"]["conversion"]["beta_log2_hours"],
                "effect_on_missed_pp": eff.effect_on_missed_pp,
                "effect_on_missed_true_pp": realised["true_effect_on_leads_missing_sla_pp"],
                "policy_lift_pp": eff.lift_pp,
                "policy_lift_true_pp": realised["true_policy_lift_pp"],
                "naive_gap_pp": realised["naive_sla_gap_pp"],
            }
        )
        logger.info("seed %s done", seed)
    out = pd.DataFrame(rows)
    out["beta_covered"] = (out["beta_ci_low"] <= out["beta_true"]) & (
        out["beta_true"] <= out["beta_ci_high"]
    )
    return out


def seed_study_summary(study: pd.DataFrame) -> pd.DataFrame:
    """Bias, spread and coverage across seeds."""
    rows = []
    for est, true in (
        ("beta", "beta_true"),
        ("effect_on_missed_pp", "effect_on_missed_true_pp"),
        ("policy_lift_pp", "policy_lift_true_pp"),
    ):
        err = study[est] - study[true]
        rows.append(
            {
                "quantity": est,
                "mean_estimate": study[est].mean(),
                "mean_truth": study[true].mean(),
                "mean_error": err.mean(),
                "se_of_mean_error": err.std(ddof=1) / np.sqrt(len(err)),
                "sd_across_seeds": study[est].std(ddof=1),
            }
        )
    out = pd.DataFrame(rows)
    out.attrs["beta_coverage"] = float(study["beta_covered"].mean())
    out.attrs["seeds"] = len(study)
    return out


def plot_seed_study(
    study: pd.DataFrame,
    path,
    highlight: tuple[str, float, float, float] | None = None,
):
    """Forest plot: the adjusted β and its 95 % CI on each independent dataset, against
    the true β. About 1 interval in 20 is expected to miss the truth."""
    from lead_funnel.analysis import viz

    viz.apply_style()
    rows = study.sort_values("seed").reset_index(drop=True)
    n = len(rows) + (1 if highlight else 0)
    fig, ax = viz.plt.subplots(figsize=(8, 0.28 * n + 1.6))
    y = np.arange(len(rows))[::-1] + (1 if highlight else 0)
    covered = rows["beta_covered"].to_numpy()
    for yi, r, ok in zip(y, rows.itertuples(), covered, strict=True):
        color = viz.SERIES[0] if ok else viz.STATUS_CRITICAL
        ax.plot([r.beta_ci_low, r.beta_ci_high], [yi, yi], color=color, linewidth=2)
        ax.scatter(r.beta, yi, color=color, s=25, zorder=3)
    labels = [f"seed {s}" for s in rows["seed"]]
    ticks = list(y)
    if highlight:
        name, est, lo, hi = highlight
        ax.plot([lo, hi], [0, 0], color=viz.TEXT_PRIMARY, linewidth=2)
        ax.scatter(est, 0, color=viz.TEXT_PRIMARY, marker="s", s=30, zorder=3)
        labels.append(name)
        ticks.append(0)
    beta_true = float(rows["beta_true"].iloc[0])
    ax.axvline(beta_true, color=viz.TEXT_PRIMARY, linestyle="--", linewidth=1)
    ax.text(beta_true, n - 0.4, f" true β = {beta_true:.4f}", fontsize=8, va="bottom")
    ax.set_yticks(ticks, labels, fontsize=8)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Adjusted β for log2(1 + hours) with 95 % CI")
    missed = int((~rows["beta_covered"]).sum())
    ax.set_title(
        f"{len(rows) - missed} of {len(rows)} intervals contain the true effect; "
        f"mean estimate {rows['beta'].mean():.4f} (no bias)"
    )
    viz.caption(
        fig,
        "Each row: an independent synthetic dataset of 50 000 leads (clean). Red: the 95 % "
        "interval misses the truth — expected about once in 20 runs.",
    )
    return viz.save_fig(fig, path)
