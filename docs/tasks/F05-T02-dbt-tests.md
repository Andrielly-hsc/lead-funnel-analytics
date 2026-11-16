# F05-T02 — Add generic and singular dbt tests

| Field | Value |
|---|---|
| **Feature** | [F05 — Data quality & profiling](../features/F05-data-quality-profiling.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F05-T01 |
| **Branch** | `feat/F05-T02-dbt-tests` |

## Description

Encode quality rules as tests with appropriate severity.

## Steps

1. Generic: `unique`, `not_null`, `relationships`, `accepted_values`
2. Singular: `assert_response_time_non_negative.sql`, `assert_converted_leads_have_opportunity.sql`
3. Set `severity: warn` for accepted known issues, `error` for blocking ones
4. Store failures: `--store-failures` for inspection

## Acceptance criteria

- [ ] `dbt test` passes with documented warnings only

## Deliverables

- `dbt/tests/*.sql`
- YAML test configs

## Why this matters (best practice)

Tests as code make quality rules reviewable and versioned — the same idea as unit tests, applied to data.

## Notes

- **Severity policy:** `error` = a rule that must hold (pipeline stops); `warn` = a *known, accepted* issue that is reported and bounded. Documented in the new register `docs/data/known_issues.md` (KI-01 … KI-08: issue, quality dimension, detecting test, row count, handling, escalation rule).
- New **error** tests: `assert_negative_response_times_are_flagged` (a negative duration must never reach averages unflagged) and `assert_opportunity_opened_after_lead_created` (cross-table consistency).
- New **warn** tests with `error_if` escalation bounds and `store_failures=true` (failing rows kept in the `audit` schema): near-duplicate leads, invalid response times, response-time outliers, late-recorded interactions.
- Completeness thresholds with `dbt_utils.not_null_proportion`: `industry` ≥ 85 %, `company_size` ≥ 80 % (error below).
- `dbt build` on seed 42: exit code 0 with exactly four warnings whose counts equal the injection log — 500 near-duplicates, 144 invalid response times, 95 outliers, 3 052 late records. 131 nodes in total.
