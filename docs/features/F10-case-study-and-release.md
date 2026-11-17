# F10 — Case study documentation & release

| Field | Value |
|---|---|
| **Status** | In Progress |
| **Priority** | Must (MoSCoW) |
| **Depends on** | [F05](F05-data-quality-profiling.md), [F08](F08-statistical-inference.md), [F09](F09-dashboard.md) |
| **Estimate** | 6 h |
| **Created** | 2026-11-15 |

## Goal

Package the work as a business case study that a recruiter understands in 2 minutes and an engineer can verify in 20.

## User story

> As a recruiter at iSYS, I want to see the challenge, solution and measurable result immediately, so that I can judge fit quickly.

## Scope

**In scope**

- README as case study
- Analytical report
- Data card and governance notes
- v1.0.0 release

**Out of scope**

- Blog post / video (optional follow-ups)

## Acceptance criteria

- [ ] README top section: Challenge → Solution → Result with 3 key numbers and 1 hero figure
- [ ] Fresh-clone reproduction verified by CI
- [ ] Tagged release `v1.0.0` with changelog

## Tasks

| ID | Task | Estimate | Status |
|---|---|---|---|
| [F10-T01](../tasks/F10-T01-readme-case-study.md) | Write the README as a case study | 2 h | Done |
| [F10-T02](../tasks/F10-T02-analysis-report.md) | Write the final analytical report | 2 h | To Do |
| [F10-T03](../tasks/F10-T03-data-card-governance.md) | Write the data card and governance notes | 1 h | To Do |
| [F10-T04](../tasks/F10-T04-release-v1.md) | Publish the repository and release v1.0.0 | 1 h | To Do |

## Syllabus topics covered

- Ops 4.6 Communicating results and uncertainties
- Ops 3.1 Roles, risks and evidence about data and decisions
- Gov 6.5 Personal data protection and balance between utility and protection
- Ops 1.1 Versioning

## Definition of Done

- All tasks are **Done** and their acceptance criteria are met
- Code merged to `main` through a Pull Request with green CI
- Documentation (README / docs) updated
- [ARCHITECTURE.md](../ARCHITECTURE.md) conventions followed (or an ADR records the deviation)
