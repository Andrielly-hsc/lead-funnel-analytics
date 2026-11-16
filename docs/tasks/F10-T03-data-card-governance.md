# F10-T03 — Write the data card and governance notes

| Field | Value |
|---|---|
| **Feature** | [F10 — Case study documentation & release](../features/F10-case-study-and-release.md) |
| **Status** | To Do |
| **Estimate** | 1 h |
| **Depends on** | F10-T02 |
| **Branch** | `feat/F10-T03-data-card-governance` |

## Description

Document data provenance, intended use and protection measures.

## Steps

1. Data card: origin (synthetic), generation process, known issues, intended and out-of-scope uses
2. Privacy measures: pseudonymisation, minimisation in marts, retention (data regenerated, nothing stored)
3. Risks of misuse: using agent-level KPIs for individual performance evaluation without context

## Acceptance criteria

- [ ] Data card follows the *Datasheets for Datasets* structure

## Deliverables

- `docs/data/data_card.md`

## Why this matters (best practice)

Governance documentation is increasingly required (GDPR, EU AI Act). Showing it in a portfolio is rare and stands out.

## Notes

_Add decisions, problems found and links to the PR here while working._
