# F03-T04 — Test the ingestion layer

| Field | Value |
|---|---|
| **Feature** | [F03 — Ingestion into the raw layer](../features/F03-ingestion-raw-layer.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | F03-T03 |
| **Branch** | `feat/F03-T04-ingestion-tests` |

## Description

Cover happy path, idempotency, failure and quarantine.

## Steps

1. Integration test with `tmp_warehouse` fixture and a tiny generated sample
2. Test row counts raw == files
3. Test idempotency and rollback

## Acceptance criteria

- [ ] Ingestion coverage ≥ 85 %

## Deliverables

- `tests/integration/test_ingestion.py`

## Why this matters (best practice)

Row-count reconciliation between source and target is the simplest and most valuable pipeline test.

## Notes

_Add decisions, problems found and links to the PR here while working._
