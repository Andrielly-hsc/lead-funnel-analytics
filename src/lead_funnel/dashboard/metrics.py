"""KPI definitions — the metric layer of the dashboard.

Each KPI is defined **once**, here: business question, SQL expression, grain, filters,
owner, target and caveats. The dashboard computes every number from these expressions,
and ``docs/metrics.md`` is generated from this module (a test keeps them in sync). That
is the answer to "why do two reports show different numbers?": there is only one
definition to disagree with.

All expressions aggregate ``marts.fct_leads`` (alias ``f``) after the base filter.
"""

from __future__ import annotations

from dataclasses import dataclass

BASE_FILTER = "not f.is_probable_duplicate"
VALID_TIME = "not f.is_response_time_invalid"


@dataclass(frozen=True)
class Metric:
    key: str
    name: str
    question: str
    sql: str
    unit: str  # count | rate | minutes | eur
    filters: str
    owner: str
    target: str
    caveat: str


METRICS: tuple[Metric, ...] = (
    Metric(
        key="leads",
        name="Leads",
        question="How many unique leads entered the CRM?",
        sql="count(*)",
        unit="count",
        filters="probable duplicates excluded (KI-01)",
        owner="Marketing",
        target="—",
        caveat="Only leads registered in the CRM (limitation L1).",
    ),
    Metric(
        key="response_rate",
        name="Response rate",
        question="What share of leads received at least one contact?",
        sql="avg(f.is_responded::int)",
        unit="rate",
        filters="probable duplicates excluded",
        owner="Head of Customer Support",
        target="≥ 98 %",
        caveat="Including duplicates would understate it (duplicates are never contacted).",
    ),
    Metric(
        key="sla_rate",
        name="SLA met",
        question="What share of leads was answered within 60 minutes?",
        sql="avg(f.is_sla_met::int)",
        unit="rate",
        filters="duplicates excluded; leads with an invalid response time drop out "
        "(is_sla_met is null for them)",
        owner="Head of Customer Support",
        target="≥ 50 %",
        caveat="Structurally 0 % for leads created outside Mon-Fri 08:00-18:00 (L6). "
        "Never-answered leads count as missed.",
    ),
    Metric(
        key="median_response_min",
        name="Median time to first response",
        question="How long does a typical lead wait for the first contact?",
        sql=f"median(f.minutes_to_first_response) filter (where {VALID_TIME})",
        unit="minutes",
        filters="answered leads with a valid response time",
        owner="Head of Customer Support",
        target="≤ 60 min",
        caveat="Median, not mean: the distribution is extremely skewed (mean ≈ 6× median).",
    ),
    Metric(
        key="p90_response_min",
        name="p90 time to first response",
        question="How long do the slowest 10 % of answered leads wait?",
        sql=f"quantile_cont(f.minutes_to_first_response, 0.9) filter (where {VALID_TIME})",
        unit="minutes",
        filters="answered leads with a valid response time",
        owner="Head of Customer Support",
        target="—",
        caveat="Dominated by leads waiting overnight or over a weekend.",
    ),
    Metric(
        key="conversion_rate",
        name="Conversion rate",
        question="What share of leads became an opportunity?",
        sql="avg(f.is_converted::int)",
        unit="rate",
        filters="probable duplicates excluded",
        owner="Sales",
        target="—",
        caveat="Differences between groups are associations, not effects: lead quality "
        "differs between groups (see reports/analysis_report.md).",
    ),
    Metric(
        key="pipeline_eur",
        name="Pipeline value",
        question="What is the expected value of the opportunities created?",
        sql="coalesce(sum(f.opportunity_amount_eur), 0)",
        unit="eur",
        filters="probable duplicates excluded",
        owner="Sales",
        target="—",
        caveat="Expected deal value at opportunity creation — pipeline, not revenue.",
    ),
    Metric(
        key="pipeline_per_lead_eur",
        name="Pipeline per lead",
        question="How much pipeline does an average lead generate?",
        sql="coalesce(sum(f.opportunity_amount_eur), 0) / count(*)",
        unit="eur",
        filters="probable duplicates excluded",
        owner="Marketing",
        target="—",
        caveat="Use to compare sources and campaigns; sensitive to a few large deals.",
    ),
    Metric(
        key="touches_per_lead",
        name="Touches per lead",
        question="How much agent effort does a lead receive?",
        sql="avg(f.n_touches)",
        unit="count",
        filters="probable duplicates excluded; leads never contacted count as 0",
        owner="Head of Customer Support",
        target="—",
        caveat="Higher for good leads (agents work them harder) — a mediator, not a driver.",
    ),
)

BY_KEY = {m.key: m for m in METRICS}


def kpi_select(where: str = "true") -> str:
    """One-row SQL computing every KPI for the leads matching ``where`` (alias ``f``)."""
    columns = ",\n    ".join(f"{m.sql} as {m.key}" for m in METRICS)
    return f"select\n    {columns}\nfrom marts.fct_leads as f\nwhere {BASE_FILTER} and ({where})"


def render_metrics_doc() -> str:
    lines = [
        "# KPI definitions",
        "",
        "> **Generated from `src/lead_funnel/dashboard/metrics.py` — do not edit by hand.**",
        "> Regenerate with `python -m lead_funnel.dashboard.metrics > docs/metrics.md`.",
        "> The dashboard computes every number from these exact expressions, and a test checks",
        "> that the headline KPIs reconcile with `sql/analysis/01_funnel_kpis.sql`.",
        "",
        f"**Grain:** one row per lead, `marts.fct_leads` (alias `f`). **Base filter:** "
        f"`{BASE_FILTER}`. Targets are illustrative business targets, not statistical ones.",
        "",
        "| KPI | Business question | Formula (SQL) | Unit | Filters | Owner | Target |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in METRICS:
        lines.append(
            f"| **{m.name}** | {m.question} | `{m.sql}` | {m.unit} | {m.filters} | "
            f"{m.owner} | {m.target} |"
        )
    lines += ["", "## Caveats", ""]
    lines += [f"- **{m.name}:** {m.caveat}" for m in METRICS]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":  # pragma: no cover
    import sys

    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stdout.write(render_metrics_doc())
