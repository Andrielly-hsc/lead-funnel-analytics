# F01-T04 — Create the test scaffolding

| Field | Value |
|---|---|
| **Feature** | [F01 — Project setup & engineering standards](../features/F01-project-setup.md) |
| **Status** | To Do |
| **Estimate** | 1 h |
| **Depends on** | F01-T03 |
| **Branch** | `feat/F01-T04-test-scaffolding` |

## Description

Prepare the test structure following the test pyramid described in the architecture.

## Steps

1. Create `tests/unit/`, `tests/integration/`, `tests/conftest.py`
2. Configure pytest in `pyproject.toml` (`testpaths`, markers `integration`, `--cov=lead_funnel`)
3. Add a first smoke test (`import lead_funnel; assert __version__`)
4. Add a `tmp_warehouse` fixture that creates a temporary DuckDB file

## Acceptance criteria

- [ ] `pytest` runs and reports coverage
- [ ] `pytest -m "not integration"` runs only unit tests

## Deliverables

- `tests/` tree
- pytest config

## Why this matters (best practice)

Fixtures in `conftest.py` avoid repeated setup code. Separating unit from integration tests keeps the feedback loop fast.

## Notes

_Add decisions, problems found and links to the PR here while working._
