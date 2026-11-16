# F02-T05 — Export files and wire the `generate` CLI

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F02-T04 |
| **Branch** | `feat/F02-T05-export-and-cli` |

## Description

Write the landing zone in multiple formats.

## Steps

1. `leads.csv`, `opportunities.csv` (UTF-8, ISO-8601 timestamps)
2. `interactions.jsonl` (one JSON object per line)
3. `agents.parquet`, `campaigns.parquet` via pyarrow
4. Write to a temp file then rename (atomic write)
5. `lead-funnel generate --seed 42 --n-leads 50000 [--clean]`

## Acceptance criteria

- [ ] Command creates all files in `data/raw/`
- [ ] Running twice with same seed produces identical file hashes

## Deliverables

- `src/lead_funnel/generator/writer.py`
- `generate` sub-command

## Why this matters (best practice)

Atomic writes prevent half-written files if the process crashes — a basic reliability practice in ingestion pipelines.

## Notes

- `lead-funnel generate [--seed N] [--n-leads N] [--clean] [--out-dir PATH]` writes to `data/raw/` by default. The seed falls back to `LF_SEED`. Heavy imports (pandas, numpy) happen inside the handler, so `lead-funnel --help` stays fast.
- Output files: `leads.csv`, `opportunities.csv`, `interactions.jsonl`, `agents.parquet`, `campaigns.parquet`, plus `_ground_truth.json` (parameters, realised effects, injection log), `_truth_leads.parquet` (per-lead true values) and `_manifest.json` (rows + SHA-256 per file). Files starting with `_` are not source data and will be ignored by ingestion.
- Timestamps in text formats are ISO 8601 UTC (`2025-01-01T07:15:43Z`); Parquet uses typed `timestamp[s, UTC]` and `date32` with an explicit Arrow schema built from `schema.py`. Pandas metadata is stripped from Parquet files (smaller, reader-agnostic).
- **Determinism verified:** two runs with seed 42 produce byte-identical files (`cmp` on all 8 files; hashes in the manifest).
- **Atomic writes:** each file goes to `.<name>.tmp` and is moved with `os.replace`, so a crash never leaves a half-written file for ingestion to pick up.
- Performance: the full 50 000-lead run takes ~13 s, ~20 MB of JSON Lines. Writing JSONL record by record with `json.dumps` was replaced by `DataFrame.to_json(lines=True)`.
- Input validation: `--n-leads` below 100 exits with code 2 and a clear message.
