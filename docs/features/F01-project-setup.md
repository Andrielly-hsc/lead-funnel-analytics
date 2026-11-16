# F01 — Project setup & engineering standards

| Field | Value |
|---|---|
| **Status** | In Progress |
| **Priority** | Must (MoSCoW) |
| **Depends on** | — |
| **Estimate** | 8 h |
| **Created** | 2026-11-15 |

## Goal

Create a professional, reproducible repository skeleton so every later feature starts from the same standards.

## User story

> As a reviewer, I want to clone the repo and run lint, tests and the pipeline with a few documented commands, so that I trust the results.

## Scope

**In scope**

- Git repository, licence, ignore rules
- Python packaging with `pyproject.toml` and `src/` layout
- Lint/format (ruff, sqlfluff), pre-commit hooks
- pytest scaffolding and coverage
- GitHub Actions CI
- Configuration and logging modules

**Out of scope**

- Cloud deployment
- Docker (not needed for a local DuckDB project; covered in project 4)

## Acceptance criteria

- [ ] `pip install -e .` works on a fresh venv with Python 3.11
- [ ] `ruff check .`, `ruff format --check .` and `pytest` pass locally and in CI
- [ ] README explains setup in ≤ 10 commands

## Tasks

| ID | Task | Estimate | Status |
|---|---|---|---|
| [F01-T01](../tasks/F01-T01-initialize-repository.md) | Initialize the Git repository | 1 h | Done |
| [F01-T02](../tasks/F01-T02-python-packaging.md) | Configure Python packaging and environment | 2 h | Done |
| [F01-T03](../tasks/F01-T03-code-quality-tooling.md) | Set up lint, format and pre-commit hooks | 1 h | To Do |
| [F01-T04](../tasks/F01-T04-test-scaffolding.md) | Create the test scaffolding | 1 h | To Do |
| [F01-T05](../tasks/F01-T05-ci-pipeline.md) | Create the GitHub Actions CI pipeline | 2 h | To Do |
| [F01-T06](../tasks/F01-T06-config-and-logging.md) | Add configuration and logging modules | 1 h | To Do |

## Syllabus topics covered

- 4.1 Python 3: modules, files, exceptions; modular organisation, tests, reproducibility
- Ops 1.1 Versioning of code · 1.3 Pipelines, tests, CI/CD · 1.4 Reproducibility
- Ops 2.4 Protection of secrets

## Definition of Done

- All tasks are **Done** and their acceptance criteria are met
- Code merged to `main` through a Pull Request with green CI
- Documentation (README / docs) updated
- [ARCHITECTURE.md](../ARCHITECTURE.md) conventions followed (or an ADR records the deviation)
