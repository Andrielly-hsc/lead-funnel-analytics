# F02-T01 — Define the domain model and data contract

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | Done |
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

- The contract lives in code (`generator/schema.py`). `docs/data/data_dictionary.md` is **generated** from it, and a unit test fails if the two disagree, so the documentation cannot silently go stale ("docs as code").
- Every parameter of the causal model is in `generator/params.py` as frozen dataclasses. Read-only mappings (`MappingProxyType`) keep them immutable.
- Causal effect of interest: each doubling of (1 + hours to first response) multiplies the conversion odds by **0.85**. `lead_score` is the confounder: it speeds up responses (−0.35 on log-minutes) and raises conversion (+0.90 on the logit). See `docs/data/causal_dag.md` for the adjustment set and the variables that must *not* be adjusted for (mediators).
- Decision: timestamps are exported in **UTC**, while business hours are defined in Europe/Berlin local time. This is a realistic pitfall the analysis has to handle (hour-of-day must be converted back).
- Decision for F04-T04: the agents export already contains **history** (one row per version with `valid_from`/`valid_to`), as an HR system export would. `dim_agent` can be built from it directly; a dbt snapshot is only needed for sources that overwrite their history.
- **CI caught a bug the laptop could not:** the `.gitignore` rule `data/` matches *any* folder named `data`, so `docs/data/` (data dictionary and causal DAG) was never committed. Tests passed locally because the files existed on disk; on a fresh CI checkout the docs-sync test failed. Fixed by anchoring the rule to the repository root (`/data/`). Two lessons: anchor ignore patterns, and `.gitignore` does not support comments on the same line as a pattern.
