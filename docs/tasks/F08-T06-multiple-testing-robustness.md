# F08-T06 — Correct for multiple testing and run robustness checks

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | F08-T05 |
| **Branch** | `feat/F08-T06-multiple-testing-robustness` |

## Description

Make results stable and honest across segments.

## Steps

1. Segment-level tests (by team, channel) with Holm and Benjamini–Hochberg corrections
2. Sensitivity: different SLA thresholds (30/60/120 min), excluding anomalies, different seeds
3. Stability table: does the conclusion change?

## Acceptance criteria

- [ ] Corrected vs uncorrected p-values shown
- [ ] Conclusion stable across ≥ 3 robustness variants (or instability explained)

## Deliverables

- `inference.py` functions
- notebook section

## Why this matters (best practice)

Testing 20 segments at α = 0.05 yields ~1 false positive by chance. Correction is not optional when you slice data.

## Notes

_Add decisions, problems found and links to the PR here while working._
