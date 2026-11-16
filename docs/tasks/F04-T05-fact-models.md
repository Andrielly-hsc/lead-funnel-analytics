# F04-T05 — Build fact models

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | Done |
| **Estimate** | 3 h |
| **Depends on** | F04-T04 |
| **Branch** | `feat/F04-T05-fact-models` |

## Description

Create the two facts with declared grain.

## Steps

1. `fct_leads` (accumulating snapshot): one row per lead with milestone timestamps, response minutes, `sla_met`, `is_converted`, amount, FKs
2. `fct_interactions` (transaction): one row per interaction with FKs to lead, agent (point-in-time join on SCD2 validity), date
3. Relationship tests from facts to every dimension
4. Add the `e2e` job to `.github/workflows/ci.yml`: generate a small sample (`--n-leads 2000`) → ingest → `dbt build` → `pytest -m integration`

## Acceptance criteria

- [ ] `relationships` tests pass
- [ ] Reconciliation: sum of converted leads == rows in `stg_crm__opportunities`

## Deliverables

- `dbt/models/marts/fct_*.sql`
- `_marts__models.yml`

## Why this matters (best practice)

Declaring the grain in the YAML description prevents the most common analytics bug: fan-out joins that multiply rows and inflate sums.

## Notes

- `fct_leads` — **accumulating snapshot**, grain one row per lead: milestones (created, first response, opportunity) as columns, SLA flags, activity counts and outcome. `fct_interactions` — **transaction fact**, grain one row per interaction, with `is_first_touch` and `is_recorded_late`.
- **Point-in-time joins** to the SCD2 `dim_agent` on the *local* event date: a lead created before an agent's team change belongs to the old team version. Verified: agent A012's leads split 858 (inbound_dach) / 558 (inbound_international) at the change date.
- Foreign keys are never null: `campaign_key` falls back to the `'-1'` "No campaign" member; `relationships` tests to every dimension.
- **Reconciliation** tests: `equal_rowcount` fact vs staging for both facts, and a singular test `assert_converted_leads_reconcile_with_opportunities` (number *and* total amount of opportunities must match the source).
- Design note: low-cardinality lead attributes (country, industry, size band, score) stay on `fct_leads` for BI convenience. A separate `dim_lead` would be 1:1 with the fact, which Kimball advises against.
- Full project: **121 dbt tests pass**, on 50 000 and on 2 000 leads. In the warehouse the naïve gap is already visible: conversion 21.2 % (SLA met) vs 11.4 % (missed).
- CI: new `e2e` job (after `test`) — generate 2 000 leads → ingest → `dbt deps` → `dbt source freshness` → `dbt build`. `deps` must run before any other dbt command, because dbt parses the whole project (including `dbt_utils` macros) first.
