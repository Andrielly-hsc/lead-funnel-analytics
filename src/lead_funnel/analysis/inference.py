"""Statistical inference for the lead funnel (F08), following reports/analysis_plan.md.

Every test returns the estimate, a 95 % confidence interval, the p-value **and** an
effect size — a p-value alone is never a result. With ~50 000 leads almost any
difference is "significant"; practical relevance is judged against the pre-registered
minimum effect of interest (+2 percentage points).
"""

from __future__ import annotations

from dataclasses import dataclass

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
