# F03-T02 — Implement idempotent loaders

| Field | Value |
|---|---|
| **Feature** | [F03 — Ingestion into the raw layer](../features/F03-ingestion-raw-layer.md) |
| **Status** | To Do |
| **Estimate** | 3 h |
| **Depends on** | F03-T01 |
| **Branch** | `feat/F03-T02-idempotent-loaders` |

## Description

Load each format into `raw.<entity>` without duplicating data.

## Steps

1. Compute SHA-256 of each file; skip if hash already in `meta.load_log` with status `success`
2. Use DuckDB `read_csv`, `read_json`, `read_parquet` with **explicit column types** (no auto-detection surprises)
3. Add metadata columns `_loaded_at`, `_source_file`, `_file_hash`
4. Wrap each file load in a transaction (`BEGIN … COMMIT`, `ROLLBACK` on error)
5. `--full-refresh` flag drops and reloads everything

## Acceptance criteria

- [ ] Second run loads 0 new rows and logs `skipped`
- [ ] Simulated failure mid-load leaves no partial rows

## Deliverables

- `src/lead_funnel/ingestion/loaders.py`
- `ingest` sub-command

## Why this matters (best practice)

*Idempotency* + *transactions* = safe retries. In production, jobs fail and get re-run; a pipeline that duplicates data on retry is the most common source of wrong KPIs.

## Notes

_Add decisions, problems found and links to the PR here while working._
