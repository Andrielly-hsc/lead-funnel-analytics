# F04-T02 — Build staging models

| Field | Value |
|---|---|
| **Feature** | [F04 — Dimensional model with dbt](../features/F04-dimensional-model-dbt.md) |
| **Status** | Done |
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

- Five staging models, one per source, following the dbt structure *import CTE → logical CTEs → final select*. Staging is the **only** place that reads `source()`.
- **Standardisation via seeds:** `channel_mapping` and `country_mapping` (lower-cased, trimmed spellings → canonical codes). A new spelling in the source makes `accepted_values` fail, which is the signal to extend the seed (documented in `_seeds.yml`).
- **Pseudonymisation:** macro `pseudonymise()` = salted SHA-256 with the salt from `LF_HASH_SALT` (dev default only). Raw e-mail and phone are dropped. Phones are reduced to digits without the `00` prefix first, so `+49 30 123` and `0049-30-123` hash identically. Note: pseudonymised data is still personal data under GDPR (Recital 26).
- Exact duplicates are removed with `qualify row_number() over (partition by lead_id ...)`. Near-duplicates are **kept** for F05.
- Renamed `source` → `lead_source` (a reserved SQL keyword, flagged by sqlfluff RF04); renaming is exactly what staging is for.
- Verification on seed-42 data: 51 510 raw rows → 50 500 unique leads (1 010 exact duplicates removed); 16 channel spellings → 4 codes; all countries → 10 ISO codes; all 500 near-duplicate pairs share `email_hash` and `phone_hash`; no raw e-mail/phone column in staging. `dbt build`: 42 tests pass.
- Tests use the dbt ≥ 1.10 syntax (`data_tests:` with `arguments:`).
- sqlfluff (jinja templater) needed `load_macros_from_path = dbt/macros` and a lint-time stand-in for `env_var`, defined in `.sqlfluff`.
