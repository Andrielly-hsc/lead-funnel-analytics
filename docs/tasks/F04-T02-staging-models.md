# F04-T02 — Build staging models

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | To Do |
| **Estimate** | 3 h |
| **Depends on** | F04-T01 |
| **Branch** | `feat/F04-T02-staging-models` |

## Description

One clean model per source table.

## Steps

1. `stg_crm__leads`, `stg_crm__interactions`, `stg_crm__agents`, `stg_crm__campaigns`, `stg_crm__opportunities`
2. Rename to conventions, cast types, trim/lowercase categories, map countries via a seed `country_codes.csv`
3. Deduplicate exact duplicates with `qualify row_number() …`
4. Pseudonymise: `sha256(lower(email) || salt)` as `email_hash`; drop raw email/phone
5. Flag (do not drop) invalid values: `is_response_time_invalid`

## Acceptance criteria

- [ ] Each staging model has PK tests
- [ ] Category columns pass `accepted_values`

## Deliverables

- `dbt/models/staging/crm/*.sql`
- `dbt/seeds/country_codes.csv`
- `_crm__models.yml`

## Why this matters (best practice)

Staging is the only place where raw columns are renamed and cast. Downstream models never touch `source()` — this keeps cleaning logic in one place.

## Notes

_Add decisions, problems found and links to the PR here while working._
