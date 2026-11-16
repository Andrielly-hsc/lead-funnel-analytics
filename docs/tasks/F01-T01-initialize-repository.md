# F01-T01 — Initialize the Git repository

| Field | Value |
|---|---|
| **Feature** | [F01 — Project setup & engineering standards](../features/F01-project-setup.md) |
| **Status** | To Do |
| **Estimate** | 1 h |
| **Depends on** | — |
| **Branch** | `feat/F01-T01-initialize-repository` |

## Description

Create the repository with the files every professional repo has, and agree on branch and commit conventions.

## Steps

1. `git init -b main`
2. Add `.gitignore` (Python template + `data/`, `*.duckdb`, `.env`, `dbt/target/`, `dbt/logs/`)
3. Add `.gitattributes` with `* text=auto eol=lf` (avoids Windows/Linux line-ending diffs)
4. Add `LICENSE` (MIT) and a `README.md` skeleton (title, one-line pitch, status badge placeholder)
5. Add `CHANGELOG.md` in *Keep a Changelog* format
6. First commit: `chore: initial repository structure`

## Acceptance criteria

- [ ] `git status` is clean after setup
- [ ] Generated files under `data/` are ignored

## Deliverables

- `.gitignore`
- `.gitattributes`
- `LICENSE`
- `README.md`
- `CHANGELOG.md`

## Why this matters (best practice)

A clean history and predictable conventions are the first thing a reviewer sees. Conventional Commits (`feat:`, `fix:`, `docs:`) make the history readable and allow automatic changelogs.

## Notes

_Add decisions, problems found and links to the PR here while working._
