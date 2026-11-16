# F03-T01 — Create the DuckDB warehouse and raw schema

| Field | Value |
|---|---|
| **Feature** | [F03 — Ingestion into the raw layer](../features/F03-ingestion-raw-layer.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
