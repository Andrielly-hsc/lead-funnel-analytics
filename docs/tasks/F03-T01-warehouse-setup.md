# F03-T01 — Create the DuckDB warehouse and raw schema

| Field | Value |
|---|---|
| **Feature** | [F03 — Ingestion into the raw layer](../features/F03-ingestion-raw-layer.md) |
| **Status** | Done |
| **Estimate** | 1 h |
| **Depends on** | — |
| **Branch** | `feat/F03-T01-warehouse-setup` |

## Description

Create the database file and schemas used by later layers.

## Steps

1. `ingestion/warehouse.py`: `connect(db_path)` context manager
2. Create schemas `raw`, `meta`
3. Table `meta.load_log(run_id, file_name, file_hash, rows, status, started_at, finished_at, error)`

## Acceptance criteria

- [ ] Schemas exist after first run
- [ ] Connection always closed (context manager)

## Deliverables

- `src/lead_funnel/ingestion/warehouse.py`

## Why this matters (best practice)

A load log is the minimum *audit trail* of a pipeline: what was loaded, when, and whether it worked.

## Notes

- `ingestion/warehouse.py`: `connect()` context manager (DuckDB **locks the file** while a connection is open, so it must always be closed), session time zone fixed to UTC, schemas `raw` and `meta`.
- `meta.load_log` is the audit trail: one row per decision (`success`, `skipped`, `rejected`, `failed`) with run id, file hash, row count, timings and message. A `CHECK` constraint rejects unknown statuses.
- Raw tables are created from the contract (`schema.py`) with DuckDB types (`TIMESTAMPTZ`, `DATE`, `BIGINT`, …) plus metadata columns `_loaded_at`, `_source_file`, `_file_hash`, `_run_id`. Raw columns are nullable on purpose: raw stores what the source sent; rules are enforced by the contract check and again in dbt.
- Dependency added: `pytz` — DuckDB needs it to return `TIMESTAMPTZ` values to Python, and pandas 3 no longer installs it.
- Third-party warning filtered *narrowly* in pytest (by exact message): DuckDB itself calls `DataFrame.drop(inplace=True)`, deprecated in pandas 3.1, when converting `TIMESTAMPTZ` to pandas. Our own deprecations still fail the tests.
