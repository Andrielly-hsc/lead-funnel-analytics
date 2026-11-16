# F02-T06 — Unit-test the generator

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | To Do |
| **Estimate** | 2 h |
| **Depends on** | F02-T05 |
| **Branch** | `feat/F02-T06-generator-tests` |

## Description

Prove determinism, schema and statistical properties.

## Steps

1. Test same seed → identical DataFrames (`pd.testing.assert_frame_equal`)
2. Test columns and dtypes match `schema.py`
3. Test injected issue rates within tolerance (large n)
4. Test no negative response times when `--clean`

## Acceptance criteria

- [ ] Generator coverage ≥ 90 %

## Deliverables

- `tests/unit/test_generator_*.py`

## Why this matters (best practice)

Testing *statistical* code means testing properties with tolerances, not exact values.

## Notes

_Add decisions, problems found and links to the PR here while working._
