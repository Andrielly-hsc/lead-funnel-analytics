# F05-T02 — Add generic and singular dbt tests

| Field | Value |
|---|---|
| **Feature** | [F05 — Data quality & profiling](../features/F05-data-quality-profiling.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
