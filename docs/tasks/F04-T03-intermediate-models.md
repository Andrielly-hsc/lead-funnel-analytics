# F04-T03 — Build intermediate models

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | Done |
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

- `int_leads__first_response` is the **single definition** of *first response* (earliest outbound interaction) and of the SLA rule (`var('sla_minutes')` = 60). Every downstream model and dashboard reuses it, so two reports can never disagree on what "SLA met" means.
- Null handling is explicit: never-answered leads have `minutes_to_first_response = null` (not 0) and `is_sla_met = false`; leads with clock skew (first contact before creation) are `is_response_time_invalid` and get `is_sla_met = null`, because their real duration is unknown. Responses later than 30 days are flagged `is_response_time_outlier`.
- `int_leads__touch_counts`: interactions per lead by type, late records (`recording_lag > 48 h`), last touch; zero for leads never contacted (left join + `coalesce`).
- Tests: `dbt_utils.equal_rowcount` against `stg_crm__leads` (no lead lost or duplicated by the joins), a conditional `not_null` (`where: not is_response_time_invalid`) and an `expression_is_true` consistency check.
- Seed-42 results match the injection log exactly: 144 invalid and 95 outlier response times, 3 052 late records, 7 783 meetings. Response rate 94.8 % (vs 95.8 % in the generator) because the 500 near-duplicate leads are never contacted — a realistic distortion that F05 will quantify. SLA met: 41.2 %; median 76.8 minutes.
