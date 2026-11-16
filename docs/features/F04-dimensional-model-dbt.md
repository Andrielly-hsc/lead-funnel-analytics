# F04 — Dimensional model with dbt

| Field | Value |
|---|---|
| **Status** | In Progress |
| **Priority** | Must (MoSCoW) |
| **Depends on** | [F03](F03-ingestion-raw-layer.md) |
| **Estimate** | 13 h |
| **Created** | 2026-11-15 |

## Goal

Transform raw data into a tested, documented star schema following dbt and Kimball best practices.

## User story

> As a BI analyst, I want clean fact and dimension tables with clear grain, so that every KPI is computed once and consistently.

## Scope

**In scope**

- dbt project with staging, intermediate, marts layers
- Star schema: `fct_leads`, `fct_interactions`, `dim_date`, `dim_agent` (SCD2), `dim_channel`, `dim_lead_source`
- Pseudonymisation of e-mail/phone in staging
- Docs and lineage graph

**Out of scope**

- Semantic layer / metrics server
- Incremental models (data volume does not require them — explained in ADR)

## Acceptance criteria

- [ ] `dbt build` passes with 0 errors
- [ ] Every model documented with description and grain
- [ ] No raw e-mail or phone in marts
- [ ] Row counts reconcile: unique leads in staging == rows in `fct_leads`

## Tasks

| ID | Task | Estimate | Status |
|---|---|---|---|
| [F04-T01](../tasks/F04-T01-dbt-project-setup.md) | Set up the dbt project | 1 h | Done |
| [F04-T02](../tasks/F04-T02-staging-models.md) | Build staging models | 3 h | Done |
| [F04-T03](../tasks/F04-T03-intermediate-models.md) | Build intermediate models | 2 h | Done |
| [F04-T04](../tasks/F04-T04-dimension-models.md) | Build dimension models (incl. SCD Type 2) | 3 h | To Do |
| [F04-T05](../tasks/F04-T05-fact-models.md) | Build fact models | 3 h | To Do |
| [F04-T06](../tasks/F04-T06-docs-and-lineage.md) | Document models and publish lineage | 1 h | To Do |

## Syllabus topics covered

- Eng 1.1 Relational and multidimensional models; normalisation and integrity
- Eng 1.2 Data warehouse and data mart
- Eng 2.1 DDL/DML, joins, aggregations, CTEs, window functions
- Eng 5.1 Metadata, catalogue and lineage
- Gov 6.1 Minimisation · 6.3 Pseudonymisation

## Definition of Done

- All tasks are **Done** and their acceptance criteria are met
- Code merged to `main` through a Pull Request with green CI
- Documentation (README / docs) updated
- [ARCHITECTURE.md](../ARCHITECTURE.md) conventions followed (or an ADR records the deviation)
