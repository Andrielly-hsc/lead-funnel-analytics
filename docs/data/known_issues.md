# Known data-quality issues

> A register of quality problems that are **known and accepted**: the pipeline does
> not stop for them, but they are measured on every run and handled explicitly.
> Each issue has a dbt test with `severity: warn` (failing rows stored in the
> `audit` schema) and an `error_if` bound that escalates to a pipeline failure if the
> volume grows abnormally. Counts below are for seed 42, 50 000 leads.

| ID | Issue | Dimension | Detected by | Rows | Handling | Escalates when |
|---|---|---|---|---:|---|---|
| KI-01 | Same person registered under several lead ids (near-duplicates) | Uniqueness | `warn_near_duplicate_leads` | 500 | Kept as separate leads; flagged `is_probable_duplicate` (F05-T04); analyses exclude duplicates | > 2 500 groups |
| KI-02 | First contact recorded *before* the lead was created (clock skew) | Validity | `warn_invalid_response_times` | 144 | `is_response_time_invalid`; `is_sla_met = null`; excluded from response-time metrics | > 1 000 leads |
| KI-03 | First response more than 30 days after creation (wrong import date) | Accuracy | `warn_response_time_outliers` | 95 | `is_response_time_outlier`; kept, analyses decide (robustness check in F08) | > 1 000 leads |
| KI-04 | Interactions stored in the CRM more than 48 h after they happened | Timeliness | `warn_late_recorded_interactions` | 3 052 | Occurrence time is correct; only near-real-time reporting is affected | > 10 000 records |
| KI-05 | `industry` missing (completely at random) | Completeness | `not_null_proportion ≥ 85 %` | 8 % | Shown as missing; not imputed | completeness < 85 % (error) |
| KI-06 | `company_size` missing, more often for web-form leads (MAR) | Completeness | `not_null_proportion ≥ 80 %` | 13.8 % | Size band `unknown`; analyses must not drop these rows silently (would under-represent web leads) | completeness < 80 % (error) |
| KI-07 | Inconsistent spellings of channel (16) and country (44) | Consistency | `accepted_values` after mapping | 5 % / 6 % | Mapped to canonical codes with seeds; a new spelling fails the test | any unmapped value (error) |
| KI-08 | Fully duplicated export rows | Uniqueness | profile (`reports/quality/profile_leads.md`) | 1 010 | Removed in staging (`qualify row_number()`) | — |

## Severity policy

| Severity | Meaning | Example |
|---|---|---|
| `error` | A rule that must hold; the pipeline stops | primary keys, relationships, reconciliation, negative response times *without* flag |
| `warn` | A known, accepted issue; reported and bounded | KI-01 … KI-04 |

Inspect the failing rows of a warning, e.g.:

```sql
select * from audit.warn_near_duplicate_leads order by n_leads desc limit 20;
```
