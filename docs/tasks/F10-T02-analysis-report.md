# F10-T02 — Write the final analytical report

| Field | Value |
|---|---|
| **Feature** | [F10 — Case study documentation & release](../features/F10-case-study-and-release.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F10-T01 |
| **Branch** | `feat/F10-T02-analysis-report` |

## Description

Executive summary plus methods for technical readers.

## Steps

1. 1-page executive summary with recommendations and confidence level
2. Methods, results tables, limitations, next steps (A/B test proposal)
3. Link every number to the notebook/SQL that produced it

## Acceptance criteria

- [ ] Every number in the report is reproducible from code

## Deliverables

- `reports/analysis_report.md`

## Why this matters (best practice)

Traceable numbers are the difference between an analysis and an opinion.

## Notes

- `reports/analysis_report.md` now opens with a one-page **executive summary**: the question, a one-sentence answer, a findings table with an explicit **confidence level per finding** (from "high" for the confounding to "medium" for the policy value and the business-hours effect), three recommendations (don't judge teams by the raw gap; A/B-test out-of-hours coverage before investing; run data-quality rules before every report) and the limits in plain language.
- New section **7 · Where each number comes from**: every figure in the report mapped to the command, results section and function that produces it. Checked: 2.49 pp × 50 000 = 1 244 opportunities × €29 323 average deal ≈ €36.5 M.
- Methods (sections 1-6, written in F08-T05) unchanged; the header now carries version, author and data description instead of the "work in progress" note.
