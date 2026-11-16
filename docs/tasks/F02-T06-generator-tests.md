# F02-T06 — Unit-test the generator

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | Done |
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

- 40 new tests in five files: contract and docs sync (`test_generator_schema`), determinism (`test_generator_determinism`), output vs contract (`test_generator_output`), funnel behaviour and **effect recovery** (`test_generator_funnel`), injected issues (`test_generator_corruption`), plus CLI `generate` tests.
- Statistical code is tested on **properties with tolerances**, not exact values: the adjusted estimate must lie within 3 standard errors of the true coefficient; observed conversion within 4 SE of the mean true probability; the naïve SLA gap must be > 1.5× the true effect.
- Business-hours logic is tested with explicit edge cases (before opening, after closing, Friday 18:00, Saturday, the Sunday of the DST switch).
- Session-scoped fixtures (`clean_data`, `dirty_data`) generate data once and share it. Plain helpers live in `tests/factories.py`, because importing from `conftest.py` is a pytest anti-pattern.
- `filterwarnings = error` for `DeprecationWarning`/`FutureWarning`: two pandas-4 deprecations (`dayofweek`, `fillna(Timestamp.max)`) were found and fixed this way, and future ones will fail CI instead of breaking silently.
- Result: **67 tests in ~8 s; 99 % line and branch coverage** (generator modules 98-100 %, acceptance ≥ 90 %).
