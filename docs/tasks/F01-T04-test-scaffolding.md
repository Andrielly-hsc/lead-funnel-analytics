# F01-T04 — Create the test scaffolding

| Field | Value |
|---|---|
| **Feature** | [F01 — Project setup & engineering standards](../features/F01-project-setup.md) |
| **Status** | Done |
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

- `--strict-markers` makes a typo such as `@pytest.mark.intergration` fail instead of silently creating a new marker.
- Branch coverage is enabled (`branch = true`): it checks that both sides of every `if` were executed, not only that each line ran.
- `tmp_warehouse` uses pytest's built-in `tmp_path`, so every test gets its own DuckDB file and nothing leaks between tests.
- Tests import the **installed** package (no `pythonpath = src` hack), which is the point of the `src/` layout.
