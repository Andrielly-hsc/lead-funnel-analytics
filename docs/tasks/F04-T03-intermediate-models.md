# F04-T03 — Build intermediate models

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | F04-T02 |
| **Branch** | `feat/F04-T03-intermediate-models` |

## Description

Encapsulate reusable business logic.

## Steps

1. `int_leads__first_response`: first outbound interaction per lead (`min(occurred_at)`), minutes to response, `sla_met`
2. `int_leads__touch_counts`: number of interactions per lead
3. Handle leads with no response (null, not zero!)

## Acceptance criteria

- [ ] Leads without interactions have `first_response_at is null`
- [ ] SLA logic defined once, parameterised by var `sla_minutes`

## Deliverables

- `dbt/models/intermediate/*.sql`

## Why this matters (best practice)

Putting business rules (what counts as a *response*?) in one model avoids each analyst computing it differently — a classic source of conflicting numbers.

## Notes

_Add decisions, problems found and links to the PR here while working._
