# F02 — Synthetic CRM data generator

| Field | Value |
|---|---|
| **Status** | In Progress |
| **Priority** | Must (MoSCoW) |
| **Depends on** | [F01](F01-project-setup.md) |
| **Estimate** | 17 h |
| **Created** | 2026-11-15 |

## Goal

Generate a realistic, reproducible CRM dataset with a **known causal effect** of response time on conversion and realistic data-quality problems.

## User story

> As an analyst, I want data whose true effects I know, so that I can prove my methods recover them and show how naïve methods are biased.

## Scope

**In scope**

- Entities: leads, interactions, agents (with team history), campaigns, opportunities
- Causal structure with a confounder (lead quality affects both response time and conversion)
- Configurable injection of data-quality issues
- Export to CSV, JSON Lines and Parquet
- Data dictionary and documented ground truth

**Out of scope**

- Free-text notes / NLP fields
- Real customer data of any kind

## Acceptance criteria

- [ ] Same seed → byte-identical files
- [ ] Ground-truth effect documented and recoverable by a correctly specified model
- [ ] Issue rates (duplicates, nulls…) match configuration within ±0.5 pp

## Tasks

| ID | Task | Estimate | Status |
|---|---|---|---|
| [F02-T01](../tasks/F02-T01-domain-and-data-contract.md) | Define the domain model and data contract | 2 h | Done |
| [F02-T02](../tasks/F02-T02-generator-core.md) | Implement the generator core (entities) | 4 h | Done |
| [F02-T03](../tasks/F02-T03-funnel-simulation.md) | Simulate funnel events with the causal effect | 4 h | Done |
| [F02-T04](../tasks/F02-T04-inject-quality-issues.md) | Inject realistic data-quality issues | 3 h | Done |
| [F02-T05](../tasks/F02-T05-export-and-cli.md) | Export files and wire the `generate` CLI | 2 h | To Do |
| [F02-T06](../tasks/F02-T06-generator-tests.md) | Unit-test the generator | 2 h | To Do |

## Syllabus topics covered

- 1.1 Data types and variables; distributions
- 2.1 Probability and distributions in applications
- 3.2 Association, prediction and causality
- Eng 3.1 Formats CSV, JSON, Parquet
- Gov 6.3 Anonymisation and pseudonymisation (fake PII)

## Definition of Done

- All tasks are **Done** and their acceptance criteria are met
- Code merged to `main` through a Pull Request with green CI
- Documentation (README / docs) updated
- [ARCHITECTURE.md](../ARCHITECTURE.md) conventions followed (or an ADR records the deviation)
