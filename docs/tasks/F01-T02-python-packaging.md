# F01-T02 — Configure Python packaging and environment

| Field | Value |
|---|---|
| **Feature** | [F01 — Project setup & engineering standards](../features/F01-project-setup.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | F01-T01 |
| **Branch** | `feat/F01-T02-python-packaging` |

## Description

Turn the code into an installable package with pinned dependencies.

## Steps

1. Create venv: `py -3.11 -m venv .venv`
2. Write `pyproject.toml` (PEP 621): name `lead-funnel`, `requires-python = ">=3.11"`, dependencies, optional `[dev]` extras, console script `lead-funnel = "lead_funnel.cli:main"`
3. Create `src/lead_funnel/__init__.py` with `__version__`
4. Pin exact versions with `pip-compile` into `requirements-lock.txt`
5. Document setup commands in README

## Acceptance criteria

- [ ] Fresh clone + documented commands → `lead-funnel --help` works
- [ ] All dependencies pinned to exact versions in the lock file

## Deliverables

- `pyproject.toml`
- `requirements-lock.txt`
- `src/lead_funnel/__init__.py`

## Why this matters (best practice)

`pyproject.toml` is the official standard for Python projects. Loose requirements (`pandas>=2`) declare compatibility; the lock file guarantees *reproducibility* — the same versions everywhere.

## Notes

_Add decisions, problems found and links to the PR here while working._
