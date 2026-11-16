"""Data-quality scorecard across the six standard dimensions.

Dimensions (DAMA-DMBOK / ISO 8000 vocabulary): completeness, uniqueness, validity,
consistency, accuracy, timeliness. Every metric is a **share of conforming rows**
with an explicit threshold, measured where it matters:

* on ``raw`` to show the quality of what the source delivers;
* on ``staging``/``marts`` to show what remains after the pipeline cleaned it.

*Accuracy* compares values with the truth, which is normally unknowable. Here the
generator's ``_truth_leads.parquet`` makes it measurable; without that file the
accuracy metrics are reported as ``n/a``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

CANONICAL_CHANNELS = "('web_form', 'email', 'phone', 'partner_referral')"
CANONICAL_COUNTRIES = "('DE', 'AT', 'CH', 'NL', 'FR', 'IT', 'ES', 'PL', 'BE', 'DK')"


@dataclass(frozen=True)
class Metric:
    """``sql`` returns one row ``(conforming, total)``."""

    dimension: str
    name: str
    layer: str
    threshold: float  # minimum share of conforming rows, 0-1
    sql: str
    needs_truth: bool = False


METRICS: tuple[Metric, ...] = (
    Metric(
        "completeness",
        "industry populated",
        "raw",
        0.90,
        "select count(industry), count(*) from raw.leads",
    ),
    Metric(
        "completeness",
        "company size populated",
        "raw",
        0.85,
        "select count(company_size), count(*) from raw.leads",
    ),
    Metric(
        "uniqueness",
        "lead rows unique by lead_id",
        "raw",
        0.99,
        "select count(distinct lead_id), count(*) from raw.leads",
    ),
    Metric(
        "uniqueness",
        "lead rows unique by lead_id",
        "staging",
        0.99,
        "select count(distinct lead_id), count(*) from staging.stg_crm__leads",
    ),
    Metric(
        "uniqueness",
        "one lead per person (e-mail)",
        "staging",
        0.995,
        "select count(distinct email_hash), count(*) from staging.stg_crm__leads",
    ),
    Metric(
        "uniqueness",
        "one lead per person, flagged duplicates excluded",
        "marts",
        0.995,
        "select count(distinct email_hash), count(*) from marts.fct_leads "
        "where not is_probable_duplicate",
    ),
    Metric(
        "validity",
        "channel is a canonical code",
        "raw",
        0.99,
        f"select count(*) filter (where channel in {CANONICAL_CHANNELS}), count(*) from raw.leads",
    ),
    Metric(
        "validity",
        "channel is a canonical code",
        "staging",
        0.99,
        f"select count(*) filter (where channel in {CANONICAL_CHANNELS}), count(*) "
        "from staging.stg_crm__leads",
    ),
    Metric(
        "validity",
        "country is an ISO code",
        "raw",
        0.99,
        f"select count(*) filter (where country in {CANONICAL_COUNTRIES}), count(*) from raw.leads",
    ),
    Metric(
        "validity",
        "country is an ISO code",
        "staging",
        0.99,
        f"select count(*) filter (where country_code in {CANONICAL_COUNTRIES}), count(*) "
        "from staging.stg_crm__leads",
    ),
    Metric(
        "validity",
        "response time not negative",
        "marts",
        0.999,
        "select count(*) filter (where minutes_to_first_response >= 0), count(*) "
        "from marts.fct_leads where is_responded",
    ),
    Metric(
        "consistency",
        "opportunity opened after lead creation",
        "staging",
        1.0,
        "select count(*) filter (where o.opened_at >= l.created_at), count(*) "
        "from staging.stg_crm__opportunities o "
        "join staging.stg_crm__leads l using (lead_id)",
    ),
    Metric(
        "consistency",
        "interaction recorded after it occurred",
        "raw",
        1.0,
        "select count(*) filter (where recorded_at >= occurred_at), count(*) from raw.interactions",
    ),
    Metric(
        "accuracy",
        "response time matches the truth (±1 min)",
        "marts",
        0.99,
        "select count(*) filter (where abs(f.minutes_to_first_response "
        "- t.true_hours_to_first_response * 60) <= 1), count(*) "
        "from marts.fct_leads f join truth t using (lead_id) where f.is_responded",
        needs_truth=True,
    ),
    Metric(
        "accuracy",
        "company size matches the truth",
        "staging",
        0.999,
        "select count(*) filter (where s.company_size = t.true_company_size), count(*) "
        "from staging.stg_crm__leads s join truth t using (lead_id) "
        "where s.company_size is not null",
        needs_truth=True,
    ),
    Metric(
        "timeliness",
        "interaction recorded within 48 h",
        "raw",
        0.99,
        "select count(*) filter (where recorded_at - occurred_at <= interval 48 hour), "
        "count(*) from raw.interactions",
    ),
)


def compute_scorecard(
    con: duckdb.DuckDBPyConnection, truth_path: Path | None = None
) -> pd.DataFrame:
    """Evaluate every metric. Returns one row per metric with value, threshold and status."""
    has_truth = truth_path is not None and truth_path.exists()
    if has_truth:
        con.execute(
            # a temp *table*: DuckDB cannot bind parameters inside a view definition
            "create or replace temp table truth as select * from read_parquet(?)",
            [str(truth_path)],
        )
    rows = []
    for m in METRICS:
        if m.needs_truth and not has_truth:
            value, conforming, total, status = None, None, None, "n/a"
        else:
            conforming, total = con.execute(m.sql).fetchone()
            value = conforming / total if total else None
            status = "n/a" if value is None else ("PASS" if value >= m.threshold else "FAIL")
        rows.append(
            {
                "dimension": m.dimension,
                "metric": m.name,
                "layer": m.layer,
                "conforming": conforming,
                "total": total,
                "value": value,
                "threshold": m.threshold,
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def to_markdown(scorecard: pd.DataFrame, figure: str | None = None) -> str:
    icon = {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "n/a": "➖ n/a"}
    by_dim = (
        scorecard[scorecard["status"] != "n/a"]
        .groupby("dimension", sort=False)["status"]
        .apply(lambda s: f"{(s == 'PASS').sum()}/{len(s)}")
    )
    lines = [
        "# Data-quality scorecard",
        "",
        "> Generated by `lead-funnel profile`. Each metric is the share of conforming rows;",
        "> **raw** = as delivered by the source, **staging/marts** = after the pipeline.",
        "> Known, accepted issues and their handling: `docs/data/known_issues.md`.",
        "",
    ]
    if figure:
        lines += [f"![Data-quality scorecard]({figure})", ""]
    lines += [
        "| Dimension | Metric | Layer | Conforming | Value | Target | Status |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for r in scorecard.itertuples(index=False):
        value = "" if r.value is None or pd.isna(r.value) else f"{100 * r.value:.2f} %"
        counts = (
            ""
            if r.total is None or pd.isna(r.total)
            else f"{int(r.conforming):,} / {int(r.total):,}"
        )
        lines.append(
            f"| {r.dimension} | {r.metric} | {r.layer} | {counts} | {value} | "
            f"≥ {100 * r.threshold:g} % | {icon[r.status]} |"
        )
    lines += ["", "## Summary by dimension (metrics passing)", ""]
    lines += [f"- **{d}:** {v}" for d, v in by_dim.items()]
    return "\n".join(lines) + "\n"


def plot_scorecard(scorecard: pd.DataFrame, path: Path) -> Path:
    """Horizontal bars of the share of *non-conforming* rows vs the allowed maximum.

    Plotting the defect rate (lower is better) instead of the conformance rate makes
    the differences visible: on a 0-100 % scale, 97 % and 99 % look identical.
    """
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.transforms import blended_transform_factory

    from lead_funnel.analysis import viz

    viz.apply_style()
    data = scorecard[scorecard["status"] != "n/a"].iloc[::-1].reset_index(drop=True)
    defect = 100 * (1 - data["value"].astype(float))
    allowed = 100 * (1 - data["threshold"])
    colors = [viz.STATUS_GOOD if s == "PASS" else viz.STATUS_CRITICAL for s in data["status"]]
    labels = [f"{r.dimension} · {r.metric} ({r.layer})" for r in data.itertuples()]

    fig, ax = viz.plt.subplots(figsize=(10, 0.42 * len(data) + 1.4))
    ax.barh(range(len(data)), defect, height=0.55, color=colors, zorder=2)
    ax.scatter(
        allowed,
        range(len(data)),
        marker="|",
        s=260,
        linewidths=2,
        color=viz.TEXT_SECONDARY,
        zorder=3,
    )
    xmax = max(defect.max(), allowed.max()) * 1.08
    # status + value in a fixed column right of the plot: never collides with bars/markers
    column = blended_transform_factory(ax.transAxes, ax.transData)
    for y, (d, s) in enumerate(zip(defect, data["status"], strict=True)):
        mark = "✓" if s == "PASS" else "✗"
        ax.text(1.02, y, f"{mark} {s}", transform=column, va="center", fontsize=9)
        ax.text(
            1.17,
            y,
            f"{d:.2f} %",
            transform=column,
            va="center",
            ha="right",
            fontsize=9,
            color=viz.TEXT_SECONDARY,
        )
    ax.set_yticks(range(len(data)), labels)
    ax.set_xlim(0, xmax)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Rows not conforming (%) — lower is better")
    failing = data["status"] == "FAIL"
    raw_fails = int((failing & (data["layer"] == "raw")).sum())
    after_fails = int((failing & (data["layer"] != "raw")).sum())
    ax.set_title(
        f"Data quality: {raw_fails} checks fail on raw data, {after_fails} still fail "
        "after the pipeline"
    )
    ax.legend(
        handles=[
            Patch(color=viz.STATUS_GOOD, label="✓ PASS"),
            Patch(color=viz.STATUS_CRITICAL, label="✗ FAIL"),
            Line2D(
                [],
                [],
                marker="|",
                linestyle="none",
                markersize=14,
                markeredgewidth=2,
                color=viz.TEXT_SECONDARY,
                label="maximum allowed",
            ),
        ],
        loc="lower right",
    )
    return viz.save_fig(fig, path)
