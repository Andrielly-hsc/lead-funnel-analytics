# F02-T04 — Inject realistic data-quality issues

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | Done |
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

- `corruption.py` injects every issue of `CorruptionParams` and returns an `InjectionLog` (affected ids and counts), saved with the ground truth so that F05 can measure **precision/recall of its own detection rules**.
- Counts are exact (`round(rate × n)` rows sampled without replacement) instead of independent coin flips, so realised rates equal the configuration and tests can be strict.
- Order of injection matters and is deliberate: near-duplicates first (they then also receive missing values and spelling variants, as real ones would), exact duplicates **last**, so duplicated rows are byte-identical.
- Missingness mechanisms: `industry` is **MCAR** (8 % of all rows); `company_size` is **MAR** (25 % for web-form leads, an optional form field, vs 3 % otherwise). Dropping rows with missing size would therefore under-represent web leads — an example for F07.
- Interaction issues: clock skew makes the first contact precede lead creation (negative response time); a "wrong import date" shifts *all* events of a lead by 30-60 days (otherwise the next follow-up would silently become the first response); late-arriving records have `recorded_at` 2-10 days after `occurred_at` (timeliness).
- `core.generate(params, seed, clean=False)` orchestrates all stages with one child RNG per stage (`STAGES` order is append-only to keep existing random streams stable).
- Seed 42 check: 51 510 lead rows (50 000 + 500 near-duplicates + 1 010 exact duplicates); 16 channel spellings; 144 negative and 95 extreme response times; 3 052 late records.
- Pitfall: `dataclasses.asdict` deep-copies values and cannot copy `MappingProxyType`; added `params.to_dict()` for JSON export.
