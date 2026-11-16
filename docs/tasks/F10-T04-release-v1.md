# F10-T04 — Publish the repository and release v1.0.0

| Field | Value |
|---|---|
| **Feature** | [F10 — Case study documentation & release](../features/F10-case-study-and-release.md) |
| **Status** | To Do |
| **Estimate** | 1 h |
| **Depends on** | F10-T03 |
| **Branch** | `feat/F10-T04-release-v1` |

## Description

Make the project public and versioned.

## Steps

1. Create GitHub repo `lead-funnel-analytics` (via `gh repo create` once GitHub CLI is installed)
2. Push `main`; verify CI green
3. Update `CHANGELOG.md`; tag `v1.0.0`; create GitHub release with notes
4. Add repo topics: `data-analytics`, `dbt`, `duckdb`, `statistics`, `sql`; pin on GitHub profile

## Acceptance criteria

- [ ] Public repo with green CI and release `v1.0.0`

## Deliverables

- GitHub repository
- release notes

## Why this matters (best practice)

Semantic versioning and releases show you treat analytics as a product with a lifecycle, not a one-off script.

## Notes

_Add decisions, problems found and links to the PR here while working._
