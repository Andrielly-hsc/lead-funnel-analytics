# F03-T03 — Validate files against the data contract

| Field | Value |
|---|---|
| **Feature** | [F03 — Ingestion into the raw layer](../features/F03-ingestion-raw-layer.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
