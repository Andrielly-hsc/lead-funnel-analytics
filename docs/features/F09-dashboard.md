# F09 — KPI dashboard

| Field | Value |
|---|---|
| **Status** | In Progress |
| **Priority** | Should (MoSCoW) |
| **Depends on** | [F06](F06-analytical-sql.md), [F08](F08-statistical-inference.md) |
| **Estimate** | 8 h |
| **Created** | 2026-11-15 |

## Goal

Give managers an interactive, honest view of funnel KPIs, including uncertainty.

## User story

> As a support manager, I want a dashboard with funnel, SLA and team KPIs and clear uncertainty, so that I don't over-react to noise.

## Scope

**In scope**

- Metric definitions document
- Streamlit app reading marts
- Uncertainty visualisation

**Out of scope**

- Authentication/multi-user hosting
- Real-time refresh

## Acceptance criteria

- [ ] App starts with one command and shows numbers identical to SQL KPI queries
- [ ] Every KPI has a tooltip/definition linked to the metric doc
- [ ] Segments with small n are flagged

## Tasks

| ID | Task | Estimate | Status |
|---|---|---|---|
| [F09-T01](../tasks/F09-T01-metric-definitions.md) | Define the KPIs (metric layer document) | 1 h | Done |
| [F09-T02](../tasks/F09-T02-streamlit-app.md) | Build the Streamlit dashboard | 3 h | Done |
| [F09-T03](../tasks/F09-T03-uncertainty-communication.md) | Communicate uncertainty in the dashboard | 1 h | Done |
| [F09-T04](../tasks/F09-T04-power-bi-optional.md) | (Optional) Build a Power BI version | 3 h | To Do |

## Syllabus topics covered

- Ops 4.2 Prioritisation, acceptance criteria and indicators
- Ops 4.6 Communicating results and uncertainty to users
- 1.1 Exploration and visualisation

## Definition of Done

- All tasks are **Done** and their acceptance criteria are met
- Code merged to `main` through a Pull Request with green CI
- Documentation (README / docs) updated
- [ARCHITECTURE.md](../ARCHITECTURE.md) conventions followed (or an ADR records the deviation)
