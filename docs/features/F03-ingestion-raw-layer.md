# F03 — Ingestion into the raw layer

| Field | Value |
|---|---|
| **Status** | Done |
| **Priority** | Must (MoSCoW) |
| **Depends on** | [F02](F02-synthetic-crm-data-generator.md) |
| **Estimate** | 8 h |
| **Created** | 2026-11-15 |

## Goal

Load landing files into DuckDB reliably: idempotent, validated, auditable.

## User story

> As a data engineer, I want every file loaded exactly once with metadata, so that I can trace and reprocess any number.

## Scope

**In scope**

- DuckDB database and `raw` schema
- Loaders for CSV, JSONL, Parquet
- Contract validation and quarantine
- Load metadata and run log
- Full and incremental modes

**Out of scope**

- Streaming ingestion (covered in project 3)
- Change Data Capture from a live database

## Acceptance criteria

- [x] Running `ingest` twice does not duplicate rows
- [x] Every raw row has `_loaded_at`, `_source_file`, `_file_hash`
- [x] A file violating the contract goes to `data/quarantine/` and the run reports it

## Tasks

| ID | Task | Estimate | Status |
|---|---|---|---|
| [F03-T01](../tasks/F03-T01-warehouse-setup.md) | Create the DuckDB warehouse and raw schema | 1 h | Done |
| [F03-T02](../tasks/F03-T02-idempotent-loaders.md) | Implement idempotent loaders | 3 h | Done |
| [F03-T03](../tasks/F03-T03-contract-validation.md) | Validate files against the data contract | 2 h | Done |
| [F03-T04](../tasks/F03-T04-ingestion-tests.md) | Test the ingestion layer | 2 h | Done |

## Syllabus topics covered

- Eng 3.1 ETL/ELT; batch, full and incremental; formats; failures, reprocessing and consistency
- Eng 1.1 Transactions and consistency
- 4.1 Python files and exceptions

## Definition of Done

- All tasks are **Done** and their acceptance criteria are met
- Code merged to `main` through a Pull Request with green CI
- Documentation (README / docs) updated
- [ARCHITECTURE.md](../ARCHITECTURE.md) conventions followed (or an ADR records the deviation)
