# F01-T06 — Add configuration and logging modules

| Field | Value |
|---|---|
| **Feature** | [F01 — Project setup & engineering standards](../features/F01-project-setup.md) |
| **Status** | Done |
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

- Settings are a **frozen dataclass** built by `get_settings(env)`. Accepting `env` as a parameter makes configuration testable without touching the real environment (dependency injection).
- Precedence: real environment variables > `.env` file (`python-dotenv`, added as a dependency) > defaults. Invalid values raise `ConfigError` with the variable name, and the CLI exits with code 2.
- CLI sub-commands are registered in one `COMMANDS` table; not-yet-built commands log which task will implement them and exit with code 1.
- **Problem found:** `logging.basicConfig(force=True)` removes every root handler, including pytest's `caplog` and any handler set by an application that imports this package. `configure_logging` now adds one named handler only once and never removes foreign handlers.
- **Lesson:** `pre-commit run --all-files` only checks files Git already tracks. New files are checked when staged, which is why the commit hook caught a line-length error that the manual run had missed. Run `git add` before the manual check.
- Removed the `PD901` ignore: that rule no longer exists in ruff 0.17.
- Result: 21 tests, 100 % line and branch coverage on `src/`.
