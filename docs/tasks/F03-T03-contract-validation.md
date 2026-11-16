# F03-T03 — Validate files against the data contract

| Field | Value |
|---|---|
| **Feature** | [F03 — Ingestion into the raw layer](../features/F03-ingestion-raw-layer.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F03-T02 |
| **Branch** | `feat/F03-T03-contract-validation` |

## Description

Reject structurally broken files before they reach the warehouse.

## Steps

1. Check required columns, types castable, primary key column not null
2. Raise `DataContractError` with a clear message; move file to `data/quarantine/`
3. Note: *content* issues (duplicates, bad categories) are **not** rejected here — they are handled in staging

## Acceptance criteria

- [ ] A file with a missing column is quarantined and logged as `rejected`

## Deliverables

- `src/lead_funnel/ingestion/contracts.py`

## Why this matters (best practice)

Distinguish *structural* errors (reject) from *quality* issues (load, then clean and measure). Rejecting too much hides problems from the business.

## Notes

- **What is rejected (structural):** missing required column; value not castable to the contract type (DuckDB raises while reading with explicit types); null in a non-nullable column (e.g. primary key); empty file. Rejected files are **moved to `data/quarantine/<run_id>__<file>`** (kept for investigation, never deleted) and the previous snapshot in `raw` stays untouched (rollback).
- **What is *not* rejected (content):** duplicates, spelling variants, outliers. They are loaded, then cleaned in staging and measured in F05. Rejecting them would hide data-quality problems from the business.
- **Schema evolution:** extra columns produce a *warning* and are ignored (an additive change is backwards compatible); reordered CSV columns are handled by reading the header first and selecting contract columns by name. A removed column is a breaking change → rejection.
- `rejected` (contract violation → quarantine) is distinguished from `failed` (any other database error → file left in place so a retry can succeed).
- Smoke test with four broken files: reordered + extra column → loaded with warning; missing `amount_eur` → rejected; `"yesterday"` as timestamp → rejected; null `campaign_id` → rejected; the three rejected files are in quarantine.
- DuckDB quirk: the JSON error message said "line 1" although the bad value was on the last line. Error *locations* from readers are not always reliable; the quarantined file is what matters.
