# F02-T02 — Implement the generator core (entities)

| Field | Value |
|---|---|
| **Feature** | [F02 — Synthetic CRM data generator](../features/F02-synthetic-crm-data-generator.md) |
| **Status** | To Do |
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

_Add decisions, problems found and links to the PR here while working._
