"""H3: effect of response time on conversion, naïve vs adjusted (reports/analysis_plan.md §3).

The adjustment set comes from the causal DAG (docs/data/causal_dag.md): lead score,
channel, source and company-size band. Mediators (touches, meetings) are never adjusted
for. The true effects of the generator are read only *after* estimating
(:func:`compare_with_truth`), to show the bias of naïve methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from matplotlib.lines import Line2D
from statsmodels.discrete.discrete_model import BinaryResultsWrapper

from lead_funnel.analysis import viz

NAIVE_SLA = "converted ~ sla_met"
NAIVE_HOURS = "converted ~ log2_hours + no_response"
ADJUSTED = (
    "converted ~ log2_hours + no_response + lead_score_10"
    " + C(channel) + C(lead_source) + C(company_size_band, Treatment('small'))"
)
BINNED = (
    "converted ~ C(response_bin, Treatment('≤ 1 h')) + lead_score_10"
    " + C(channel) + C(lead_source) + C(company_size_band, Treatment('small'))"
)
POLICY_HOURS = 0.5  # the counterfactual policy: every lead answered within 30 minutes
SLA_HOURS = 1.0


class ModelDidNotConverge(RuntimeError):
    """Maximum likelihood did not converge — the estimates must not be used."""


def fit(formula: str, df: pd.DataFrame) -> BinaryResultsWrapper:
    """Fit a logistic model and refuse to return a non-converged one.

    The usual cause is (quasi-)complete **separation**: a category in which every lead
    converted, or none did (e.g. zero conversions among never-answered leads in a small
    sample). Its coefficient then runs off to ±∞ and every other estimate is unreliable.
    Remedies: more data, merging sparse categories, or a penalised (Firth) model.
    """
    import warnings

    from statsmodels.tools.sm_exceptions import ConvergenceWarning

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)  # handled explicitly below
        model = smf.logit(formula, df).fit(disp=0, maxiter=100)
    if not model.mle_retvals["converged"]:
        largest = model.params.abs().idxmax()
        raise ModelDidNotConverge(
            f"logistic model did not converge (largest coefficient: {largest} = "
            f"{model.params[largest]:.1f}); likely separation — check sparse categories"
        )
    return model


@dataclass(frozen=True)
class Coefficient:
    term: str
    estimate: float
    se: float
    ci: tuple[float, float]
    p_value: float

    @property
    def odds_ratio(self) -> float:
        return float(np.exp(self.estimate))

    @property
    def odds_ratio_ci(self) -> tuple[float, float]:
        return float(np.exp(self.ci[0])), float(np.exp(self.ci[1]))


def coefficient(model: BinaryResultsWrapper, term: str) -> Coefficient:
    lo, hi = model.conf_int().loc[term]
    return Coefficient(
        term=term,
        estimate=float(model.params[term]),
        se=float(model.bse[term]),
        ci=(float(lo), float(hi)),
        p_value=float(model.pvalues[term]),
    )


def average_marginal_effect(model: BinaryResultsWrapper, term: str) -> tuple[float, float, float]:
    """Average change in conversion probability (in pp) per unit of ``term``, with 95 % CI."""
    m = model.get_margeff(at="overall").summary_frame()
    row = m.loc[term]
    return 100 * row["dy/dx"], 100 * row["Conf. Int. Low"], 100 * row["Cont. Int. Hi."]


def vif_table(df: pd.DataFrame) -> pd.DataFrame:
    """Variance inflation factors of the adjusted model's design matrix (no intercept)."""
    from patsy import dmatrix
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    X = dmatrix(ADJUSTED.split("~", 1)[1], df, return_type="dataframe")
    cols = [c for c in X.columns if c != "Intercept"]
    values = [variance_inflation_factor(X.to_numpy(), X.columns.get_loc(c)) for c in cols]
    return pd.DataFrame({"term": cols, "vif": values}).sort_values("vif", ascending=False)


def calibration_table(
    model: BinaryResultsWrapper, df: pd.DataFrame, bins: int = 10
) -> pd.DataFrame:
    """Mean predicted vs observed conversion by decile of predicted probability."""
    pred = model.predict(df)
    decile = pd.qcut(pred, bins, labels=False, duplicates="drop")
    t = pd.DataFrame({"pred": pred, "obs": df["converted"], "decile": decile})
    return t.groupby("decile").agg(
        n=("obs", "size"), predicted=("pred", "mean"), observed=("obs", "mean")
    )


# ----------------------------------------------------------------------------------
# g-computation: from a model coefficient to a business effect
# ----------------------------------------------------------------------------------
def policy_frame(df: pd.DataFrame, policy_hours: float = POLICY_HOURS) -> pd.DataFrame:
    """The same leads under the policy "answered within ``policy_hours``"."""
    cf = df.copy()
    # clip at 0: leads with clock-skew errors have negative hours, and log2(1 + h) is
    # undefined for h < -1 (only relevant when errors are deliberately included)
    observed = np.clip(df["hours"], 0, None)
    hours = np.where(df["no_response"] == 1, policy_hours, np.minimum(observed, policy_hours))
    cf["log2_hours"] = np.log2(1 + hours)
    cf["no_response"] = 0
    return cf


@dataclass(frozen=True)
class PolicyEffect:
    observed: float  # mean predicted conversion as observed
    policy: float  # mean predicted conversion under the policy
    effect_on_missed_pp: float  # mean change for answered leads that missed the SLA

    @property
    def lift_pp(self) -> float:
        return 100 * (self.policy - self.observed)


def g_computation(
    model: BinaryResultsWrapper, df: pd.DataFrame, sla_hours: float = SLA_HOURS
) -> PolicyEffect:
    """Standardisation: predict every lead under observed and counterfactual response time
    with the *adjusted* model, holding its covariates fixed, and average the difference."""
    p_obs = model.predict(df)
    p_pol = model.predict(policy_frame(df))
    missed = (df["no_response"] == 0) & (df["hours"] > sla_hours)
    return PolicyEffect(
        observed=float(p_obs.mean()),
        policy=float(p_pol.mean()),
        effect_on_missed_pp=float(100 * (p_pol[missed] - p_obs[missed]).mean()),
    )


def bootstrap_policy(df: pd.DataFrame, resamples: int = 200, seed: int = 42) -> pd.DataFrame:
    """Non-parametric bootstrap of the whole procedure (refit + g-computation)."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(resamples):
        sample = df.iloc[rng.integers(0, len(df), len(df))].reset_index(drop=True)
        model = fit(ADJUSTED, sample)
        eff = g_computation(model, sample)
        rows.append(
            {
                "beta": model.params["log2_hours"],
                "lift_pp": eff.lift_pp,
                "effect_on_missed_pp": eff.effect_on_missed_pp,
            }
        )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------
# Checks: functional form and stratification
# ----------------------------------------------------------------------------------
RESPONSE_BINS = ["≤ 1 h", "1-4 h", "4-24 h", "> 24 h", "never answered"]


def add_response_bins(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["response_bin"] = pd.cut(
        out["hours"], [-np.inf, 1, 4, 24, np.inf], labels=RESPONSE_BINS[:4]
    ).astype(str)
    out.loc[out["no_response"] == 1, "response_bin"] = "never answered"
    return out


def binned_model_table(df: pd.DataFrame) -> pd.DataFrame:
    """Adjusted odds ratios per response-time bin vs "≤ 1 h": a check of the log2 form.
    If log2(1 + hours) is right, the odds ratios fall steadily with each later bin."""
    model = fit(BINNED, add_response_bins(df))
    rows = [{"response_bin": "≤ 1 h", "odds_ratio": 1.0, "ci_low": np.nan, "ci_high": np.nan}]
    for b in RESPONSE_BINS[1:]:
        term = f"C(response_bin, Treatment('≤ 1 h'))[T.{b}]"
        c = coefficient(model, term)
        rows.append(
            {
                "response_bin": b,
                "odds_ratio": c.odds_ratio,
                "ci_low": c.odds_ratio_ci[0],
                "ci_high": c.odds_ratio_ci[1],
            }
        )
    return pd.DataFrame(rows)


def stratified_gap(df: pd.DataFrame, strata: int = 5) -> pd.DataFrame:
    """SLA conversion gap within lead-score quintiles vs overall.

    If lead quality confounds the comparison, the gap *within* strata of similar quality
    is smaller than the overall (crude) gap — the mechanism behind Simpson's paradox.
    """
    d = df.assign(
        score_quintile=pd.qcut(df["lead_score"], strata, labels=False, duplicates="drop") + 1
    )
    rows = []
    for q, g in d.groupby("score_quintile"):
        met, missed = g[g["sla_met"]], g[~g["sla_met"]]
        rows.append(
            {
                "score_quintile": int(q),
                "n": len(g),
                "share_sla_met": g["sla_met"].mean(),
                "conv_met": met["converted"].mean(),
                "conv_missed": missed["converted"].mean(),
                "gap_pp": 100 * (met["converted"].mean() - missed["converted"].mean()),
            }
        )
    t = pd.DataFrame(rows)
    crude = 100 * (
        d.loc[d["sla_met"], "converted"].mean() - d.loc[~d["sla_met"], "converted"].mean()
    )
    weighted = float(np.average(t["gap_pp"], weights=t["n"]))
    t.attrs.update(crude_gap_pp=crude, stratified_gap_pp=weighted)
    return t


# ----------------------------------------------------------------------------------
# Naïve vs adjusted vs truth
# ----------------------------------------------------------------------------------
def compare_with_truth(
    naive_gap_pp: tuple[float, float, float],
    naive_hours: Coefficient,
    adjusted: Coefficient,
    policy: PolicyEffect,
    policy_ci: pd.DataFrame,
    truth: dict,
) -> pd.DataFrame:
    """The project's key table. ``truth`` is ``_ground_truth.json`` (used only here)."""
    beta_true = truth["params"]["conversion"]["beta_log2_hours"]
    realised = truth["realised"]
    q = policy_ci.quantile([0.025, 0.975])

    def row(name, label, estimate, lo, hi, true_value, unit):
        return {
            "quantity": name,
            "label": label,
            "estimate": estimate,
            "ci_low": lo,
            "ci_high": hi,
            "truth": true_value,
            "unit": unit,
            "truth_in_ci": lo <= true_value <= hi,
        }

    return pd.DataFrame(
        [
            row(
                "Odds ratio per doubling of (1 + hours) — naïve",
                "naïve",
                naive_hours.odds_ratio,
                *naive_hours.odds_ratio_ci,
                float(np.exp(beta_true)),
                "odds ratio",
            ),
            row(
                "Odds ratio per doubling of (1 + hours) — adjusted",
                "adjusted",
                adjusted.odds_ratio,
                *adjusted.odds_ratio_ci,
                float(np.exp(beta_true)),
                "odds ratio",
            ),
            row(
                "Conversion gain for leads that missed the SLA — naïve gap",
                "missed SLA: naïve gap",
                *naive_gap_pp,
                realised["true_effect_on_leads_missing_sla_pp"],
                "pp",
            ),
            row(
                "Conversion gain for leads that missed the SLA — adjusted",
                "missed SLA: adjusted",
                policy.effect_on_missed_pp,
                q.loc[0.025, "effect_on_missed_pp"],
                q.loc[0.975, "effect_on_missed_pp"],
                realised["true_effect_on_leads_missing_sla_pp"],
                "pp",
            ),
            row(
                "Policy lift: everyone answered within 30 min — adjusted",
                "all within 30 min: adjusted",
                policy.lift_pp,
                q.loc[0.025, "lift_pp"],
                q.loc[0.975, "lift_pp"],
                realised["true_policy_lift_pp"],
                "pp",
            ),
        ]
    )


def plot_effect_comparison(table: pd.DataFrame, path: Path) -> Path:
    """Estimates with 95 % CIs next to the true value, for the two scales of the effect."""
    viz.apply_style()
    fig, (ax1, ax2) = viz.plt.subplots(1, 2, figsize=(12, 3.8), width_ratios=[1, 1.2])
    panels = (
        (ax1, table[table["unit"] == "odds ratio"], "Odds ratio per doubling of (1 + hours)"),
        (ax2, table[table["unit"] == "pp"], "Conversion gain (percentage points)"),
    )
    for ax, t, title in panels:
        labels = list(t["label"])
        y = np.arange(len(t))[::-1]
        colors = [viz.SERIES[1] if "naïve" in lab else viz.SERIES[0] for lab in labels]
        ax.errorbar(
            t["estimate"],
            y,
            xerr=[t["estimate"] - t["ci_low"], t["ci_high"] - t["estimate"]],
            fmt="none",
            ecolor=viz.TEXT_PRIMARY,
            elinewidth=1.2,
            capsize=3,
            zorder=2,
        )
        ax.scatter(t["estimate"], y, s=70, color=colors, zorder=3)
        ax.scatter(
            t["truth"],
            y,
            marker="D",
            s=55,
            facecolor="none",
            edgecolor=viz.TEXT_PRIMARY,
            linewidth=1.5,
            zorder=4,
        )
        for yi, est in zip(y, t["estimate"], strict=True):
            ax.annotate(
                f"{est:.2f}",
                (est, yi),
                textcoords="offset points",
                xytext=(0, 9),
                ha="center",
                fontsize=8,
            )
        ax.set_yticks(y, labels)
        ax.grid(axis="y", visible=False)
        ax.set_title(title)
        ax.set_ylim(-0.7, len(t) - 0.3)
    handles = [
        Line2D([], [], marker="o", linestyle="none", color=viz.SERIES[1], label="naïve estimate"),
        Line2D(
            [], [], marker="o", linestyle="none", color=viz.SERIES[0], label="adjusted estimate"
        ),
        Line2D(
            [],
            [],
            marker="D",
            linestyle="none",
            markerfacecolor="none",
            markeredgecolor=viz.TEXT_PRIMARY,
            label="true value",
        ),
        Line2D([], [], color=viz.TEXT_PRIMARY, label="95 % CI"),
    ]
    ax1.legend(handles=handles, loc="center", fontsize=8)  # empty area between the rows
    naive = table.iloc[2]
    adjusted = table.iloc[3]
    fig.suptitle(
        f"The naïve comparison claims +{naive['estimate']:.1f} pp; after adjusting for lead "
        f"quality the effect is +{adjusted['estimate']:.1f} pp — the truth is "
        f"+{adjusted['truth']:.1f} pp",
        x=0.01,
        ha="left",
        fontweight="bold",
        fontsize=12,
    )
    fig.tight_layout()
    viz.caption(
        fig,
        "Diamonds: true values known from the synthetic data generator. Adjusted = logistic "
        "model with lead score, channel, source and company size; CIs for pp effects from 200 "
        "bootstrap refits.",
    )
    return viz.save_fig(fig, path)
