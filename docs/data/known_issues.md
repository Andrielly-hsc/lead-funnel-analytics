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

## Limitations of the source (what the data cannot tell us)

These are not errors that cleaning can fix. They limit which conclusions are valid and
must be repeated wherever results are presented (F08 report, F09 dashboard). The CRM is
**administrative data**: it was collected to run the support process, not to answer
research questions.

| # | Limitation | Consequence for the analysis |
|---|---|---|
| L1 | **Selection:** only leads that reached the CRM exist. Prospects who gave up before submitting a form, or calls nobody logged, are invisible. | Conversion rates describe *registered* leads, not market demand. |
| L2 | **Response time is measured, not designed:** agents choose whom to answer first, and they favour high-score leads. | Faster-answered leads differ systematically from slower ones (confounding) — a raw SLA comparison is *not* a causal effect (F08). |
| L3 | **Measurement error** on the key variable: clock skew (KI-02) and wrong import dates (KI-03) distort response times for 0.5 % of leads. | Flagged rows are excluded or tested for robustness; residual undetected errors would bias effects towards zero. |
| L4 | **Missingness is not random:** `company_size` is missing 8× more often for web-form leads (MAR, KI-06); `industry` looks MCAR (~8 % in every channel). | Dropping rows with missing size under-represents web leads; analyses keep an explicit `unknown` category or model the missingness. |
| L5 | **One year, one organisation:** seasonality, staffing and routing rules of 2025 only. | Results may not transfer to other periods or teams (external validity); weekly trends cover 51 complete ISO weeks. |
| L6 | **Process-imposed structure:** no one works outside Mon-Fri 08:00-18:00, so leads created then can *never* meet a 60-minute SLA. | Part of the SLA gap is a staffing-policy effect, not agent behaviour; compare like with like (business-hours leads). |
| L7 | **Unobserved drivers:** budget, urgency or the contact person's role are not recorded. | Possible unmeasured confounding remains even after adjustment; only an experiment can rule it out. |

The data is synthetic (ADR-0004), so these limitations were *designed in* — which is
exactly what makes them measurable here and instructive for real administrative data.
