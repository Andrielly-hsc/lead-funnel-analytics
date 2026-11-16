# F02-T01 — Define the domain model and data contract

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | — |
| **Branch** | `feat/F02-T01-domain-and-data-contract` |

## Description

Specify every entity, column, type, allowed values and the causal assumptions *before* writing code.

## Steps

1. Write `docs/data/data_dictionary.md`: entity, column, type, nullable, allowed values, description
2. Draw the causal DAG (mermaid): `lead_quality → response_time`, `lead_quality → conversion`, `response_time → conversion`, `channel → response_time`, `source → lead_quality`
3. Fix the ground truth, e.g. *each extra hour until first response multiplies conversion odds by 0.85*; SLA-met true lift
4. Define the contract as code: `generator/schema.py` with column names and dtypes

## Acceptance criteria

- [ ] Data dictionary covers 100 % of generated columns
- [ ] Ground truth parameters listed in one place (`generator/params.py`)

## Deliverables

- `docs/data/data_dictionary.md`
- `docs/data/causal_dag.md`
- `src/lead_funnel/generator/schema.py`
- `src/lead_funnel/generator/params.py`

## Why this matters (best practice)

A *data contract* is an agreement between producer and consumer about the shape and meaning of data. Writing it first is how mature data teams avoid “surprise” schema changes.

## Notes

_Add decisions, problems found and links to the PR here while working._
