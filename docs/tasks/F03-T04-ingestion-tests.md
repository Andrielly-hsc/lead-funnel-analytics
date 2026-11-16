# F03-T04 — Test the ingestion layer

| Field | Value |
|---|---|
| **Feature** | [F03 — Ingestion into the raw layer](../features/F03-ingestion-raw-layer.md) |
| **Status** | Done |
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

- 18 ingestion tests (`tests/integration/test_ingestion.py`) + 8 warehouse tests. A small landing zone (400 leads) is generated **once per session** and copied into each test's `tmp_path`, so tests can break files without affecting each other.
- **Row-count reconciliation:** rows in every `raw.<entity>` equal the rows declared in the generator's `_manifest.json`.
- **Idempotency:** a second run skips all 5 files and duplicates nothing; a changed file *replaces* only its own snapshot; `--full-refresh` reloads all.
- **Contract violations** (parametrised): missing column, null primary key, uncastable timestamp, empty file → `rejected`, file quarantined, raw table untouched, one `rejected` row in the load log. A rejected update keeps the **previous snapshot** (rollback).
- **Schema evolution:** reordered + extra column → loaded with a warning, extra column not stored.
- **Non-contract failure:** a simulated `duckdb.IOException` (monkeypatched) → `failed`, rollback, file left in place for a retry.
- CLI exit codes: 0 (loaded or all skipped), 1 (a file rejected), 2 (no landing folder).
- Coverage: `loaders.py` 99 %, `contracts.py` and `warehouse.py` 100 %; full suite 92 tests, 99 %.
