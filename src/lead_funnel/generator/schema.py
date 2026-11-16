"""Data contract of the synthetic CRM export.

This module is the single, machine-readable definition of every source entity:
column names, logical types, nullability, allowed values and meaning. It is used by

* the generator (column order of the written files);
* the tests (schema checks);
* the ingestion contract validation (F03-T03);
* ``docs/data/data_dictionary.md`` (human-readable version, kept in sync by a test).

Nullability describes the *contract as published by the source system*. The
generator injects quality issues only where a column is declared nullable or where
the issue is a value problem (e.g. inconsistent spelling) rather than a type problem.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from lead_funnel.generator import params as p

LogicalType = Literal["string", "integer", "float", "boolean", "timestamp", "date"]
FileFormat = Literal["csv", "jsonl", "parquet"]


@dataclass(frozen=True)
class Column:
    name: str
    type: LogicalType
    nullable: bool
    description: str
    allowed: tuple[str, ...] | None = None  # canonical values (before corruption)


@dataclass(frozen=True)
class Entity:
    name: str
    file_name: str
    format: FileFormat
    grain: str
    primary_key: str
    columns: tuple[Column, ...]

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]


LEADS = Entity(
    name="leads",
    file_name="leads.csv",
    format="csv",
    grain="One row per lead as exported by the CRM (the export may contain duplicates).",
    primary_key="lead_id",
    columns=(
        Column("lead_id", "string", False, "CRM identifier of the lead, e.g. `L0000001`."),
        Column("created_at", "timestamp", False, "When the lead entered the CRM (UTC)."),
        Column("channel", "string", False, "How the lead reached us.", p.CHANNELS),
        Column("source", "string", False, "Marketing source of the lead.", p.SOURCES),
        Column("campaign_id", "string", True, "Campaign active at creation (paid, social, event)."),
        Column("country", "string", False, "ISO 3166-1 alpha-2 country code.", p.COUNTRIES),
        Column("industry", "string", True, "Industry of the company.", p.INDUSTRIES),
        Column("company_name", "string", False, "Fictional company name."),
        Column("company_size", "integer", True, "Number of employees (self-reported)."),
        Column("lead_score", "integer", False, "Marketing lead score, 0-100 (higher = better)."),
        Column("email", "string", False, "Fake contact e-mail on a reserved `.example` domain."),
        Column("phone", "string", False, "Fake contact phone number."),
        Column("owner_agent_id", "string", False, "Agent the lead was routed to."),
    ),
)

INTERACTIONS = Entity(
    name="interactions",
    file_name="interactions.jsonl",
    format="jsonl",
    grain="One row per outbound contact attempt by an agent.",
    primary_key="interaction_id",
    columns=(
        Column("interaction_id", "string", False, "Identifier of the event, e.g. `I0000001`."),
        Column("lead_id", "string", False, "Lead contacted."),
        Column("agent_id", "string", False, "Agent who made the contact."),
        Column("event_type", "string", False, "Kind of contact.", p.EVENT_TYPES),
        Column("occurred_at", "timestamp", False, "When the contact happened (UTC)."),
        Column("recorded_at", "timestamp", False, "When the CRM stored the event (UTC)."),
        Column("duration_s", "integer", False, "Duration of the contact in seconds."),
    ),
)

AGENTS = Entity(
    name="agents",
    file_name="agents.parquet",
    format="parquet",
    grain="One row per agent *version*: a new row each time an agent changes team.",
    primary_key="agent_id, valid_from",
    columns=(
        Column("agent_id", "string", False, "Agent identifier, e.g. `A001`."),
        Column("team", "string", False, "Team the agent belonged to in this period.", p.TEAMS),
        Column("seniority", "string", False, "Experience level.", p.SENIORITY),
        Column("valid_from", "date", False, "First day of this version (inclusive)."),
        Column("valid_to", "date", True, "Last day of this version (exclusive); null = current."),
    ),
)

CAMPAIGNS = Entity(
    name="campaigns",
    file_name="campaigns.parquet",
    format="parquet",
    grain="One row per marketing campaign.",
    primary_key="campaign_id",
    columns=(
        Column("campaign_id", "string", False, "Campaign identifier, e.g. `C001`."),
        Column("campaign_name", "string", False, "Human-readable name."),
        Column("source", "string", False, "Marketing source.", p.CAMPAIGN_SOURCES),
        Column("start_date", "date", False, "First day (inclusive)."),
        Column("end_date", "date", False, "Last day (inclusive)."),
        Column("budget_eur", "float", False, "Planned budget in euros."),
    ),
)

OPPORTUNITIES = Entity(
    name="opportunities",
    file_name="opportunities.csv",
    format="csv",
    grain="One row per opportunity created from a converted lead.",
    primary_key="opportunity_id",
    columns=(
        Column("opportunity_id", "string", False, "Identifier, e.g. `O000001`."),
        Column("lead_id", "string", False, "Lead that converted."),
        Column("opened_at", "timestamp", False, "When the opportunity was opened (UTC)."),
        Column("amount_eur", "float", False, "Expected deal value in euros."),
    ),
)

ENTITIES: dict[str, Entity] = {
    e.name: e for e in (LEADS, INTERACTIONS, AGENTS, CAMPAIGNS, OPPORTUNITIES)
}


# ----------------------------------------------------------------------------------
# Human-readable documentation (docs as code)
# ----------------------------------------------------------------------------------
DICTIONARY_HEADER = """# Data dictionary — synthetic CRM export

> **Generated from `src/lead_funnel/generator/schema.py` — do not edit by hand.**
> Regenerate with `python -m lead_funnel.generator.schema > docs/data/data_dictionary.md`.
> A unit test fails if this file and the code disagree.

All timestamps are **UTC** in ISO 8601. Business hours are defined in local time
(Europe/Berlin), so convert before analysing hour-of-day or weekday patterns.
All personal-looking data (e-mail, phone, company name) is **fictional**.
"""


def render_data_dictionary() -> str:
    parts = [DICTIONARY_HEADER]
    for e in ENTITIES.values():
        parts.append(f"\n## `{e.name}`\n")
        parts.append(f"- **File:** `data/raw/{e.file_name}` ({e.format})")
        parts.append(f"- **Grain:** {e.grain}")
        parts.append(f"- **Primary key:** `{e.primary_key}`\n")
        parts.append("| Column | Type | Nullable | Allowed values | Description |")
        parts.append("|---|---|---|---|---|")
        for c in e.columns:
            allowed = ", ".join(f"`{v}`" for v in c.allowed) if c.allowed else ""
            nullable = "yes" if c.nullable else "no"
            parts.append(f"| `{c.name}` | {c.type} | {nullable} | {allowed} | {c.description} |")
    return "\n".join(parts) + "\n"


if __name__ == "__main__":  # pragma: no cover
    import sys

    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stdout.write(render_data_dictionary())
