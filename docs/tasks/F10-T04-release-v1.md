# F10-T04 — Publish the repository and release v1.0.0

| Field | Value |
|---|---|
| **Feature** | [F10 — Case study documentation & release](../features/F10-case-study-and-release.md) |
| **Status** | Done |
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

- Version bumped to **1.0.0** in `pyproject.toml`, `lead_funnel.__version__` and `dbt_project.yml` (Semantic Versioning: first public, stable release of the case study).
- `CHANGELOG.md`: the accumulated *Unreleased* entries became `[1.0.0] - 2026-11-17`, with the case-study documentation added and compare/release links at the bottom (Keep a Changelog format).
- Repository public since F01, topics already set, CI green on every PR.
- Full suite before release: 177 tests passed, 91 % coverage.
- **Remaining after merge:** tag `v1.0.0` on the merge commit in `main`, create the GitHub release with notes from the changelog, pin the repo on the profile.
