# F05-T01 — Profile raw data

| Field | Value |
|---|---|
| **Feature** | [F05 — Data quality & profiling](../features/F05-data-quality-profiling.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | — |
| **Branch** | `feat/F05-T01-profiling` |

## Description

Describe each raw table before cleaning.

## Steps

1. `quality/profiling.py`: per column — type, % null, distinct count, min/max, top values, pattern checks
2. Use DuckDB `SUMMARIZE` as a fast baseline
3. Output `reports/quality/profile_<table>.md`
4. `lead-funnel profile` sub-command

## Acceptance criteria

- [ ] Profile produced for every raw table

## Deliverables

- `src/lead_funnel/quality/profiling.py`
- `reports/quality/`

## Why this matters (best practice)

Profiling first, cleaning second: you can't define rules for data you haven't looked at.

## Notes

- `quality/profiling.py` + `lead-funnel profile`: per column — type, % null, distinct, % unique, min/max, mean/std/median for numbers, top-5 values for low-cardinality text; per table — rows and fully duplicated rows. Output: `reports/quality/profile_<table>.md` (committed for seed 42, 50 000 leads).
- **Exact, not approximate:** DuckDB `SUMMARIZE` is fast but its distinct count is a HyperLogLog *estimate* — it reported 52 417 distinct `lead_id`s in a table of 51 510 rows. A quality report needs exact numbers, so the profile uses `count(distinct)`.
- Load-metadata columns (`_loaded_at`, `_run_id` …) are excluded, so the report only changes when the data changes (reviewable diffs).
- New setting `LF_REPORTS_DIR` (default `reports`).
- What the raw profile already reveals: 1 010 fully duplicated lead rows; 16 channel and 44 country spellings; `company_size` 13.8 % null, `industry` 8.0 % null; **50 235 distinct e-mails for 50 500 lead ids** — the first trace of near-duplicates (265 share the exact e-mail, the others differ only in letter case).
- pandas pitfall: storing `None` in a DataFrame column turns it into `NaN`, which is *truthy*; the "top values" filter printed `nan` until empty strings were used instead.
