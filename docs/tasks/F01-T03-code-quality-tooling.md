# F01-T03 — Set up lint, format and pre-commit hooks

| Field | Value |
|---|---|
| **Feature** | [F01 — Project setup & engineering standards](../features/F01-project-setup.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
