# F02-T02 — Implement the generator core (entities)

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | Done |
| **Estimate** | 4 h |
| **Depends on** | F02-T01 |
| **Branch** | `feat/F02-T02-generator-core` |

## Description

Generate agents, campaigns and leads with realistic distributions.

## Steps

1. Use `rng = np.random.default_rng(seed)` passed into every function
2. Agents: ~40 agents in 4 teams; 10 % change team once (for SCD2)
3. Leads: arrival times with weekday/hour seasonality (non-homogeneous Poisson), channel/source categorical mix, `lead_score` latent quality ~ Beta, company_size log-normal
4. Fake PII (`email`, `phone`) built from random tokens — never real-looking person names
5. Return pandas DataFrames; no file I/O inside these functions

## Acceptance criteria

- [ ] Distributions plotted in a scratch notebook look plausible
- [ ] Functions are pure (seed in → DataFrame out)

## Deliverables

- `src/lead_funnel/generator/entities.py`

## Why this matters (best practice)

Separating *generation* (pure functions) from *writing* (I/O) makes the code testable. Explicit RNG objects make randomness reproducible and parallel-safe.

## Notes

- The contract lives in code (`generator/schema.py`). `docs/data/data_dictionary.md` is **generated** from it, and a unit test fails if the two disagree, so the documentation cannot silently go stale ("docs as code").
- Every parameter of the causal model is in `generator/params.py` as frozen dataclasses. Read-only mappings (`MappingProxyType`) keep them immutable.
- Causal effect of interest: each doubling of (1 + hours to first response) multiplies the conversion odds by **0.85**. `lead_score` is the confounder: it speeds up responses (−0.35 on log-minutes) and raises conversion (+0.90 on the logit). See `docs/data/causal_dag.md` for the adjustment set and the variables that must *not* be adjusted for (mediators).
- Decision: timestamps are exported in **UTC**, while business hours are defined in Europe/Berlin local time. This is a realistic pitfall the analysis has to handle (hour-of-day must be converted back).
- Decision for F04-T04: the agents export already contains **history** (one row per version with `valid_from`/`valid_to`), as an HR system export would. `dim_agent` can be built from it directly; a dbt snapshot is only needed for sources that overwrite their history.
