# F10-T03 — Write the data card and governance notes

| Field | Value |
|---|---|
| **Feature** | [F10 — Case study documentation & release](../features/F10-case-study-and-release.md) |
| **Status** | Done |
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

- `docs/data/data_card.md`, structured after *Datasheets for Datasets* (Gebru et al.): motivation, composition (files, row counts, grain, why there is no real person in the data, deliberate defects, no sensitive attributes), generation process and what it does **not** model, preprocessing and protection, intended and **out-of-scope uses**, distribution, maintenance.
- **Governance as if the data were real:** GDPR principles mapped to concrete project choices — minimisation (no direct identifiers in marts), pseudonymisation ≠ anonymisation (salt must be secret; Recital 26), accuracy (precision-first duplicate rule), storage limitation (nothing persisted; a real deployment needs a retention period for raw exports and quarantine).
- **Misuse risks named explicitly:** using agent-level KPIs to rate individuals, generalising synthetic distributions to real funnels, and calling pipeline value "revenue".
- Row counts taken from the seed-42 `_manifest.json`.
