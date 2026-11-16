# F02-T04 — Inject realistic data-quality issues

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | To Do |
| **Estimate** | 3 h |
| **Depends on** | F02-T03 |
| **Branch** | `feat/F02-T04-inject-quality-issues` |

## Description

Make the data look like a real CRM export.

## Steps

1. Exact duplicates (~2 %) and near-duplicates (same email, different lead_id, ~1 %)
2. Missing values: `industry` (MCAR 8 %), `company_size` (MAR, more missing for web leads)
3. Inconsistent categories: `'Web'`, `'web '`, `'WEB_FORM'`; country `'DE'`, `'Germany'`, `'deu'`
4. Clock skew: 0.3 % negative response times; extreme outliers (> 30 days)
5. Late-arriving interactions (event date before ingestion batch)
6. All rates configurable in `params.py` and logged to `_ground_truth.json`

## Acceptance criteria

- [ ] Each issue type is present and its rate matches config ±0.5 pp
- [ ] Issues can be switched off (`--clean`)

## Deliverables

- `src/lead_funnel/generator/corruption.py`

## Why this matters (best practice)

Knowing *which* issues were injected lets the quality feature (F05) measure accuracy of its own detection — rarely possible with real data.

## Notes

_Add decisions, problems found and links to the PR here while working._
