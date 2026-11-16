# F01-T03 — Set up lint, format and pre-commit hooks

| Field | Value |
|---|---|
| **Feature** | [F01 — Project setup & engineering standards](../features/F01-project-setup.md) |
| **Status** | Done |
| **Estimate** | 1 h |
| **Depends on** | F01-T02 |
| **Branch** | `feat/F01-T03-code-quality-tooling` |

## Description

Automate style so code reviews focus on logic, not formatting.

## Steps

1. Configure `ruff` in `pyproject.toml` (rules: E, F, I, B, UP, SIM; line length 100)
2. Add `.sqlfluff` with `dialect = duckdb`, `templater = dbt`
3. Add `.pre-commit-config.yaml` with ruff, ruff-format, sqlfluff, end-of-file-fixer, check-yaml, check-added-large-files
4. `pre-commit install` and run on all files

## Acceptance criteria

- [ ] `pre-commit run --all-files` passes
- [ ] A badly formatted file is fixed automatically on commit

## Deliverables

- `.pre-commit-config.yaml`
- `.sqlfluff`
- ruff section in `pyproject.toml`

## Why this matters (best practice)

Teams agree on a formatter and stop arguing about style. `ruff` replaced black + isort + flake8 in most new projects because it is one tool and very fast.

## Notes

- Hook versions pinned with `pre-commit autoupdate` and **aligned with the lock file** (ruff 0.17.5, sqlfluff 4.5.0), so the editor/CLI and the git hook never disagree.
- Ruff rule sets: `E`, `W`, `F`, `I`, `B`, `UP`, `SIM` plus `PD` (pandas-vet) and `NPY` (catches the legacy global `np.random.seed`, which the architecture forbids).
- The hook id `ruff` is now a legacy alias; the config uses `ruff-check`.
- `.sqlfluff` uses the `jinja` templater for now. The dbt templater needs a dbt project, so the switch was added as a step to F04-T01.
- Verified: a sample uppercase query is flagged by CP01/CP02 (lowercase keywords/identifiers, dbt style guide).
