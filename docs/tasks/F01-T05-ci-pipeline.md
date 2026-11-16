# F01-T05 — Create the GitHub Actions CI pipeline

| Field | Value |
|---|---|
| **Feature** | [F01 — Project setup & engineering standards](../features/F01-project-setup.md) |
| **Status** | Done |
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

- Two jobs: `lint` (pre-commit, the same hooks as locally, so CI and laptop never disagree) and `test` (needs `lint`).
- `test` runs on **Ubuntu and Windows** (matrix, `fail-fast: false`) because portability is a quality goal and development happens on Windows.
- `permissions: contents: read` (least privilege) and `concurrency` (cancel outdated runs) are standard hardening/cost practices.
- pip and pre-commit caches keyed on the lock/config files: a new run only re-downloads when dependencies change.
- The end-to-end job was moved to F04-T05 as an explicit step, because it needs the dbt project.
- First run on GitHub ([run 43884505547](https://github.com/Andrielly-hsc/lead-funnel-analytics/actions/runs/43884505547)) was green on all three jobs (lint 29 s, Ubuntu tests 22 s, Windows tests 1 min).
- That run warned that `actions/cache@v4` targets the deprecated Node.js 20 runtime. All actions were bumped to their current majors (`checkout@v7`, `setup-python@v7`, `cache@v6`) in the first real Pull Request. **Tip:** read CI annotations even when the run is green; deprecations break pipelines months later.
