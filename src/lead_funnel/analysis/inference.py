"""Statistical inference for the lead funnel (F08), following reports/analysis_plan.md.

Every test returns the estimate, a 95 % confidence interval, the p-value **and** an
effect size — a p-value alone is never a result. With ~50 000 leads almost any
difference is "significant"; practical relevance is judged against the pre-registered
minimum effect of interest (+2 percentage points).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import confint_proportions_2indep, proportion_confint

ALPHA = 0.05
MIN_EFFECT_PP = 2.0  # pre-registered minimum effect of practical interest
OUTLIER_DAYS = 30


# ----------------------------------------------------------------------------------
# Analysis frame
# ----------------------------------------------------------------------------------
def analysis_frame(leads: pd.DataFrame, *, exclude_errors: bool = True) -> pd.DataFrame:
    """Model-ready columns from ``eda.load_leads()`` output (duplicates already excluded).

    * ``exclude_errors`` drops leads with an invalid (clock skew) or implausible
      (> 30 days) response time — their true response time is unknown (plan §2).
    * Never-answered leads stay: ``no_response = 1``, ``log2_hours = 0`` and
      ``sla_met = False``.
    """
    df = leads.copy()
    if exclude_errors:
        df = df[~(df["is_response_time_invalid"] | df["is_response_time_outlier"])]
    hours = df["minutes_to_first_response"] / 60
    df["hours"] = hours
    df["no_response"] = (~df["is_responded"]).astype(int)
    df["log2_hours"] = np.where(df["is_responded"], np.log2(1 + hours.clip(lower=0)), 0.0)
    df["sla_met"] = df["is_sla_met"].fillna(False).astype(bool)
    df["converted"] = df["is_converted"].astype(int)
    df["lead_score_10"] = df["lead_score"] / 10  # coefficient = effect of +10 score points
    df["business_hours"] = (df["iso_day_of_week"] <= 5) & df["local_hour"].between(8, 17)
    return df.reset_index(drop=True)


# ----------------------------------------------------------------------------------
# H1: difference between two proportions
# ----------------------------------------------------------------------------------
@dataclass(frozen=True)
class ProportionTest:
    n1: int
    x1: int
    n2: int
    x2: int
    p1: float
    p2: float
    diff: float  # p1 - p2
    diff_ci: tuple[float, float]  # Newcombe hybrid score interval
    p1_ci: tuple[float, float]  # Wilson
    p2_ci: tuple[float, float]  # Wilson
    z: float
    p_value: float
    chi2: float
    chi2_p_value: float
    relative_risk: float
    odds_ratio: float
    cohens_h: float

    @property
    def significant(self) -> bool:
        return self.p_value < ALPHA

    @property
    def practically_relevant(self) -> bool:
        """The CI lies entirely beyond the minimum effect of interest."""
        return min(abs(self.diff_ci[0]), abs(self.diff_ci[1])) * 100 >= MIN_EFFECT_PP and (
            np.sign(self.diff_ci[0]) == np.sign(self.diff_ci[1])
        )


def cohens_h(p1: float, p2: float) -> float:
    """Effect size for proportions: difference of arcsine-transformed rates.
    Rule of thumb (Cohen): 0.2 small, 0.5 medium, 0.8 large."""
    return 2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2))


def two_proportion_test(x1: int, n1: int, x2: int, n2: int) -> ProportionTest:
    """Two-sided z-test (pooled), χ² test, CIs and effect sizes for p1 vs p2."""
    p1, p2 = x1 / n1, x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    se = np.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se
    table = np.array([[x1, n1 - x1], [x2, n2 - x2]])
    chi2, chi2_p, _, _ = stats.chi2_contingency(table, correction=False)
    diff_lo, diff_hi = confint_proportions_2indep(x1, n1, x2, n2, method="newcomb", compare="diff")
    return ProportionTest(
        n1=n1,
        x1=x1,
        n2=n2,
        x2=x2,
        p1=p1,
        p2=p2,
        diff=p1 - p2,
        diff_ci=(float(diff_lo), float(diff_hi)),
        p1_ci=tuple(float(v) for v in proportion_confint(x1, n1, method="wilson")),
        p2_ci=tuple(float(v) for v in proportion_confint(x2, n2, method="wilson")),
        z=float(z),
        p_value=float(2 * stats.norm.sf(abs(z))),
        chi2=float(chi2),
        chi2_p_value=float(chi2_p),
        relative_risk=p1 / p2,
        odds_ratio=(p1 / (1 - p1)) / (p2 / (1 - p2)),
        cohens_h=float(cohens_h(p1, p2)),
    )


def sla_conversion_test(df: pd.DataFrame) -> ProportionTest:
    """H1: conversion of SLA-met vs SLA-missed leads (``analysis_frame`` output)."""
    met, missed = df[df["sla_met"]], df[~df["sla_met"]]
    return two_proportion_test(
        int(met["converted"].sum()), len(met), int(missed["converted"].sum()), len(missed)
    )


def bootstrap_diff_ci(
    x1: int, n1: int, x2: int, n2: int, *, resamples: int = 10_000, seed: int = 42
) -> tuple[float, float]:
    """Percentile bootstrap CI for p1 − p2.

    Resampling n Bernoulli outcomes with replacement and counting the successes is
    exactly a Binomial(n, p̂) draw, so the non-parametric bootstrap of a proportion can be
    done with ``rng.binomial`` — same result, a fraction of the memory.
    """
    rng = np.random.default_rng(seed)
    d = rng.binomial(n1, x1 / n1, resamples) / n1 - rng.binomial(n2, x2 / n2, resamples) / n2
    lo, hi = np.percentile(d, [2.5, 97.5])
    return float(lo), float(hi)


def proportion_test_table(results: dict[str, ProportionTest]) -> pd.DataFrame:
    """One row per population/comparison, in percentage points where it helps reading."""
    rows = []
    for name, t in results.items():
        rows.append(
            {
                "comparison": name,
                "n_met": t.n1,
                "n_missed": t.n2,
                "conv_met": t.p1,
                "conv_missed": t.p2,
                "diff_pp": 100 * t.diff,
                "diff_ci_pp": f"[{100 * t.diff_ci[0]:.2f}, {100 * t.diff_ci[1]:.2f}]",
                "z": t.z,
                "p_value": t.p_value,
                "relative_risk": t.relative_risk,
                "odds_ratio": t.odds_ratio,
                "cohens_h": t.cohens_h,
                "practically_relevant": t.practically_relevant,
            }
        )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------
# Correlation
# ----------------------------------------------------------------------------------
def correlation_table(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Pearson and Spearman correlation for every pair of columns (pairwise complete).

    Pearson measures *linear* association and is dominated by extreme values; Spearman
    correlates ranks, so it captures any monotonic relation and is robust to skew and
    outliers — the right default for variables like response time.
    """
    rows = []
    for i, a in enumerate(columns):
        for b in columns[i + 1 :]:
            pair = df[[a, b]].dropna()
            r, r_p = stats.pearsonr(pair[a], pair[b])
            rho, rho_p = stats.spearmanr(pair[a], pair[b])
            rows.append(
                {
                    "x": a,
                    "y": b,
                    "n": len(pair),
                    "pearson_r": float(r),
                    "pearson_p": float(r_p),
                    "spearman_rho": float(rho),
                    "spearman_p": float(rho_p),
                }
            )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------
# One-way ANOVA with assumption checks
# ----------------------------------------------------------------------------------
@dataclass(frozen=True)
class AnovaResult:
    groups: pd.DataFrame  # n, mean, sd, median per group
    shapiro_p: dict[str, float]  # normality, on a random subsample per group
    levene_p: float  # equal variances (Brown-Forsythe: centred on the median)
    f: float
    f_p: float
    welch_f: float
    welch_p: float
    kruskal_h: float
    kruskal_p: float
    eta_squared: float
    omega_squared: float
    tukey: pd.DataFrame

    @property
    def recommended_test(self) -> str:
        """Welch when variances differ; it does not assume equal variances."""
        return "welch" if self.levene_p < ALPHA else "classic"

    @property
    def recommended_p(self) -> float:
        return self.welch_p if self.recommended_test == "welch" else self.f_p


def one_way_anova(
    values: pd.Series, groups: pd.Series, *, shapiro_n: int = 500, seed: int = 42
) -> AnovaResult:
    """Classic and Welch ANOVA, Kruskal-Wallis, effect sizes and Tukey HSD post-hoc.

    Shapiro-Wilk runs on a random subsample of ``shapiro_n`` per group: on tens of
    thousands of points it rejects normality for negligible deviations, which is why
    Q-Q plots (``plot_qq``) are the primary check and the test only a supplement.
    """
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    from statsmodels.stats.oneway import anova_oneway

    data = pd.DataFrame({"value": values, "group": groups}).dropna()
    samples = {g: s["value"].to_numpy() for g, s in data.groupby("group")}
    rng = np.random.default_rng(seed)
    shapiro = {
        g: float(stats.shapiro(rng.choice(v, size=min(shapiro_n, len(v)), replace=False))[1])
        for g, v in samples.items()
    }
    f, f_p = stats.f_oneway(*samples.values())
    welch = anova_oneway(data["value"], data["group"], use_var="unequal")
    h, h_p = stats.kruskal(*samples.values())

    grand = data["value"].mean()
    ss_between = sum(len(v) * (v.mean() - grand) ** 2 for v in samples.values())
    ss_total = float(((data["value"] - grand) ** 2).sum())
    k, n = len(samples), len(data)
    ms_within = (ss_total - ss_between) / (n - k)
    tukey = pairwise_tukeyhsd(data["value"], data["group"], alpha=ALPHA)
    tukey_df = pd.DataFrame(tukey.summary().data[1:], columns=tukey.summary().data[0])

    return AnovaResult(
        groups=data.groupby("group")["value"].agg(["count", "mean", "std", "median"]),
        shapiro_p=shapiro,
        levene_p=float(stats.levene(*samples.values(), center="median")[1]),
        f=float(f),
        f_p=float(f_p),
        welch_f=float(welch.statistic),
        welch_p=float(welch.pvalue),
        kruskal_h=float(h),
        kruskal_p=float(h_p),
        eta_squared=ss_between / ss_total,
        omega_squared=(ss_between - (k - 1) * ms_within) / (ss_total + ms_within),
        tukey=tukey_df,
    )


def anova_summary(results: dict[str, AnovaResult]) -> pd.DataFrame:
    rows = []
    for name, r in results.items():
        rows.append(
            {
                "hypothesis": name,
                "n": int(r.groups["count"].sum()),
                "levene_p": r.levene_p,
                "min_shapiro_p": min(r.shapiro_p.values()),
                "anova_F": r.f,
                "anova_p": r.f_p,
                "welch_F": r.welch_f,
                "welch_p": r.welch_p,
                "kruskal_p": r.kruskal_p,
                "eta_sq": r.eta_squared,
                "omega_sq": r.omega_squared,
                "test_used": r.recommended_test,
                "reject_H0": r.recommended_p < ALPHA,
            }
        )
    return pd.DataFrame(rows)


CALLS_SQL = """
select c.channel, i.duration_s
from marts.fct_interactions as i
inner join marts.fct_leads as f on i.lead_key = f.lead_key
inner join marts.dim_channel as c on f.channel_key = c.channel_key
where i.event_type = 'call' and not f.is_probable_duplicate
"""


def load_calls(con) -> pd.DataFrame:
    """Call durations with the lead's channel (for H2b)."""
    return con.execute(CALLS_SQL).df()


def plot_qq(values: pd.Series, groups: pd.Series, path: Path, *, title: str) -> Path:
    """Q-Q plots of within-group residuals: raw scale vs log10 scale, side by side."""
    from lead_funnel.analysis import viz

    viz.apply_style()
    data = pd.DataFrame({"v": values, "g": groups}).dropna()
    data = data[data["v"] > 0]
    fig, axes = viz.plt.subplots(1, 2, figsize=(10, 4.2))
    for ax, (label, series) in zip(
        axes, (("raw scale", data["v"]), ("log10 scale", np.log10(data["v"]))), strict=True
    ):
        resid = series - series.groupby(data["g"]).transform("mean")
        z = (resid - resid.mean()) / resid.std()
        sample = np.sort(z.sample(min(len(z), 3_000), random_state=0).to_numpy())
        theoretical = stats.norm.ppf((np.arange(1, len(sample) + 1) - 0.5) / len(sample))
        ax.scatter(theoretical, sample, s=6, color=viz.SERIES[0], alpha=0.5, zorder=2)
        lim = max(abs(theoretical).max(), 4)
        ax.plot([-lim, lim], [-lim, lim], color=viz.TEXT_PRIMARY, linewidth=1, linestyle="--")
        ax.set_ylim(-4.5, max(4.5, float(sample.max()) * 1.05))
        ax.set_xlabel("Theoretical normal quantiles")
        ax.set_ylabel("Standardised residuals")
        skew = float(stats.skew(resid))
        ax.set_title(f"{label}: skewness {skew:.1f}")
    fig.suptitle(title, x=0.01, ha="left", fontweight="bold", fontsize=12)
    fig.tight_layout()
    viz.caption(fig, "Residuals = value − group mean; random sample of 3 000 points shown.")
    return viz.save_fig(fig, path)
