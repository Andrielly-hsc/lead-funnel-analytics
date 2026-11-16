# F02-T05 — Export files and wire the `generate` CLI

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
