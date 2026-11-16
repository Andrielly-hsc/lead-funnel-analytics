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

- Every function is pure: parameters + `numpy.random.Generator` in, DataFrame out. The orchestrator (F02-T05) gives each stage its **own child generator** via `SeedSequence(seed).spawn(n)`, so changing one stage never changes the random draws of another stage.
- Arrivals: weekday/weekend factor × seasonality × growth trend, and hour-of-day profiles drawn in **local time** (Europe/Berlin), then converted to UTC. DST gaps and overlaps are resolved explicitly (`nonexistent="shift_forward"`, `ambiguous=False`).
- Routing rule (`routed_team`): partner referrals → partner team; 1000+ employees → enterprise; DACH → inbound_dach; otherwise inbound_international. The agent is drawn among members of that team **on the creation date** (point-in-time).
- Fake PII: e-mails use the reserved `.example` top-level domain (RFC 2606), so they can never belong to a real person.
- Sanity check with seed 42 and 50 000 leads (< 1 s): 7.3 % of leads arrive at weekends and 77 % during business hours; mean score from 42 (social) to 59 (partner); 4 agents change team; every lead has an owner.
- **pandas 3 pitfall:** `DatetimeIndex.dayofweek` returns an `Index`, not a NumPy array (`.sum()` fails). Converted explicitly with `np.asarray`. `Series.dt.dayofweek` is deprecated in favour of `day_of_week`.
- Lint (`PD008`) flagged `.at[]` writes inside a loop; the team changes are now applied to the list of row dicts *before* building the DataFrame, which is simpler and faster.
