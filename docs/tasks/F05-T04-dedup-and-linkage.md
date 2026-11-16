# F05-T04 — Detect near-duplicates and assess false-match risk

| Field | Value |
|---|---|
| **Feature** | [F05 — Data quality & profiling](../features/F05-data-quality-profiling.md) |
| **Status** | To Do |
| **Estimate** | 3 h |
| **Depends on** | F05-T03 |
| **Branch** | `feat/F05-T04-dedup-and-linkage` |

## Description

Go beyond exact duplicates: same person, different `lead_id`.

## Steps

1. Blocking on `email_hash`, then on normalised phone + company
2. Fuzzy similarity (e.g. `rapidfuzz`) on company name; threshold sweep
3. Measure precision/recall against injected near-duplicates
4. Write a short analysis: cost of false merges (two customers merged → wrong attribution, privacy risk) vs missed duplicates

## Acceptance criteria

- [ ] Precision/recall table for at least 3 thresholds
- [ ] Chosen threshold justified by error costs

## Deliverables

- `src/lead_funnel/quality/dedup.py`
- `reports/quality/dedup_analysis.md`

## Why this matters (best practice)

Wrongly merging two people is often worse than missing a duplicate (GDPR accuracy principle). Showing you weigh that trade-off is a mature signal.

## Notes

_Add decisions, problems found and links to the PR here while working._
