# F05-T04 — Detect near-duplicates and assess false-match risk

| Field | Value |
|---|---|
| **Feature** | [F05 — Data quality & profiling](../features/F05-data-quality-profiling.md) |
| **Status** | Done |
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

- **Two parts:** (1) a deterministic rule in dbt — `int_leads__duplicates` → `fct_leads.is_probable_duplicate` / `duplicate_of_lead_id` (same normalised e-mail **or** phone, compared as salted hashes; the earliest lead is the master); (2) `quality/dedup.py`, which *justifies* the rule by comparing strategies against the 500 injected pairs. Report: `reports/quality/dedup_analysis.md`, produced by `lead-funnel profile`.
- **Results (seed 42):**

  | Strategy | Precision | Recall |
  |---|---:|---:|
  | e-mail exactly as typed | 1.000 | 0.530 |
  | normalised e-mail / normalised phone / either (chosen) | 1.000 | 1.000 |
  | fuzzy company name ≥ 80 | 0.011 | 1.000 |
  | identical company name (≥ 100) | 0.073 | 1.000 |

  Normalisation (lower-casing e-mails, digits-only phones) doubles recall at no cost in precision. Company names do not identify *people*: even an identical name gives 6 304 false matches for 500 real ones.
- **Error costs:** a false merge (two people combined) can expose one customer's data to another and is hard to undo (GDPR art. 5(1)(d)/(f)); a missed match mostly biases internal metrics. Automatic flagging must therefore favour precision; fuzzy matching could at most feed a human-review queue. Caveat for real data: shared mailboxes (`info@`) make a shared e-mail not always the same person.
- **Impact on metrics:** the 500 duplicates are never contacted. Excluding them, the response rate is 95.77 % — the generator's true rate — instead of 94.83 %. New scorecard metric *one lead per person, flagged duplicates excluded* = 100 % (PASS).
- **Performance:** fuzzy blocking (country + first 3 letters) yields ~12 M same-block pairs; a pandas self-merge took ~65 s. Moving the self-join to DuckDB, with the 14-day window applied *inside* the join, cut the full comparison to ~12 s.
- Report text lives in a package template (`quality/templates/dedup_report.md`, read with `importlib.resources`) instead of long strings in code: content separated from logic, and lint stays clean.
- Dependency: `rapidfuzz` declared directly (it was already present transitively via dbt's `metricflow` — a direct use must be a direct dependency). One `pip-compile` run failed transiently while building metadata for a metricflow version; a re-run succeeded.
- CLI happy path of `profile` (needs `dbt build`) is exercised by the CI e2e job; the unit/integration suite covers the error path.
