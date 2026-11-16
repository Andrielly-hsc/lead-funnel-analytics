# F01-T05 — Create the GitHub Actions CI pipeline

| Field | Value |
|---|---|
| **Feature** | [F01 — Project setup & engineering standards](../features/F01-project-setup.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | F01-T04 |
| **Branch** | `feat/F01-T05-ci-pipeline` |

## Description

Run quality checks automatically on every push and pull request.

## Steps

1. Create `.github/workflows/ci.yml` triggered on `push` and `pull_request` to `main`
2. Job steps: checkout → setup-python 3.11 with pip cache → install lock + package → ruff → sqlfluff → pytest unit
3. Add an end-to-end job: generate small sample → ingest → `dbt build` → integration tests (enabled once F04 exists)
4. Add CI status badge to README
5. Add `.github/pull_request_template.md` (task ID, what/why, checklist)

## Acceptance criteria

- [ ] Pipeline is green on `main`
- [ ] A failing test makes the PR check red

## Deliverables

- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`

## Why this matters (best practice)

Continuous Integration proves that the project works on a machine other than yours — the strongest reproducibility evidence a portfolio can show.

## Notes

_Add decisions, problems found and links to the PR here while working._
