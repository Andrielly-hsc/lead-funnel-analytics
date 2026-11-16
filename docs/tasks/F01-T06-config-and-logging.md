# F01-T06 — Add configuration and logging modules

| Field | Value |
|---|---|
| **Feature** | [F01 — Project setup & engineering standards](../features/F01-project-setup.md) |
| **Status** | To Do |
| **Estimate** | 1 h |
| **Depends on** | F01-T05 |
| **Branch** | `feat/F01-T06-config-and-logging` |

## Description

Centralise paths, parameters and logging so no module hard-codes them.

## Steps

1. `config.py`: a frozen dataclass `Settings` reading env vars (`LF_DATA_DIR`, `LF_DB_PATH`, `LF_SEED`, `LF_SLA_MINUTES`) with defaults
2. `.env.example` documenting every variable
3. `logging_setup.py`: one function configuring format `%(asctime)s %(levelname)s %(name)s %(message)s`
4. `cli.py` skeleton with `argparse` sub-commands (`generate`, `ingest`, `profile`, `report`)

## Acceptance criteria

- [ ] No absolute paths anywhere in `src/`
- [ ] `lead-funnel --help` lists the sub-commands

## Deliverables

- `src/lead_funnel/config.py`
- `src/lead_funnel/logging_setup.py`
- `src/lead_funnel/cli.py`
- `.env.example`

## Why this matters (best practice)

This is the *12-factor app* principle: configuration lives in the environment, not in code. The same pattern later protects real secrets (API keys, passwords).

## Notes

_Add decisions, problems found and links to the PR here while working._
