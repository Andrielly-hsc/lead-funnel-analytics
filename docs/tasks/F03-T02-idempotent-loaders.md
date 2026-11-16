# F03-T02 — Implement idempotent loaders

| Field | Value |
|---|---|
| **Feature** | [F03 — Ingestion into the raw layer](../features/F03-ingestion-raw-layer.md) |
| **Status** | Done |
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

- **Load semantics (decision):** each landing file is a *full snapshot* of its entity, as CRM exports are. Loading replaces `raw.<entity>` with `DELETE` + `INSERT` inside **one transaction**, so readers see the old or the new snapshot, never a mix. Any error → `ROLLBACK`, table untouched, `failed` row in the load log.
- **Incremental (default) vs full refresh:** a file is reloaded only if its SHA-256 differs from the hash of the content currently in the table; otherwise it is `skipped`. `--full-refresh` reloads everything. Event-level incremental loads (watermarks, append/merge) are deferred to the streaming project, because snapshot exports do not need them.
- **Explicit types, no auto-detection:** `read_csv(auto_detect = false, columns = {...})`, `read_json(columns = {...})` and casts on `read_parquet`, all generated from `schema.py`. Auto-detection guesses from a sample and can change silently between files.
- **No SQL injection:** file paths are passed as bound parameters (`?`), never concatenated. Only column names from our own contract are interpolated.
- `lead-funnel ingest [--full-refresh] [--raw-dir PATH]`: exit code 1 if any file is rejected or failed, so a scheduler or CI notices.
- Verified on a 300-lead sample: run 1 loads 5 files; run 2 skips 5 (idempotent); full refresh reloads without duplicating (309 rows, 1 run id). Each file loads in ~0.02 s.
- Observation: a client that does not set `TimeZone = 'UTC'` shows `TIMESTAMPTZ` values in its own local zone (here America/Sao_Paulo). The stored instant is the same; only the rendering differs. That is why `connect()` fixes the session zone.
- DuckDB's progress bar is disabled in `connect()` to keep pipeline logs clean.
