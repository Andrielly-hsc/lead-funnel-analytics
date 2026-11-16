# F08-T05 — Write the causal reasoning and limitations section

| Field | Value |
|---|---|
| **Feature** | [F08 — Statistical inference & relationships](../features/F08-statistical-inference.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F08-T04 |
| **Branch** | `feat/F08-T05-causality-and-limitations` |

## Description

Be explicit about what the data can and cannot prove.

## Steps

1. Present the DAG and the adjustment set (backdoor criterion, in plain language)
2. Alternative explanations: reverse causality (agents prioritise promising leads), unmeasured confounders, selection bias
3. Representativeness: does this period/sample reflect future leads?
4. Recommendation: run a randomised experiment (A/B on routing) to confirm

## Acceptance criteria

- [ ] Section reviewed against the checklist in ARCHITECTURE §6.4

## Deliverables

- `reports/analysis_report.md` section

## Why this matters (best practice)

In real administrative data you never know the truth; recommending an experiment shows you know how to *get* causal evidence.

## Notes

- `reports/analysis_report.md` (sections 1-6; the executive summary follows in F10-T02): why the raw +9.6 pp gap is confounded; the causal graph and, in plain language, the backdoor criterion and adjustment set; why mediators (follow-ups, meetings) must *not* be adjusted for; adjusted results with the truth; the multi-seed explanation of the narrowly-missing intervals; the robustness table; a threat-by-threat table of alternative explanations; and an experiment proposal.
- **Main conclusions:** about two thirds of the naïve gap is confounding; the adjusted effect is real and practically relevant (+3.6 pp for leads that missed the SLA; OR 0.83 per doubling of the wait). Policy translation: answering every lead within 30 minutes ≈ +2.5 pp ≈ 1 250 opportunities ≈ €36 M of pipeline a year (pipeline, not revenue). The business-hours result (+1.9 pp) shows the gain is concentrated in leads waiting overnight or at weekends → the recommendation targets **coverage hours**, not daytime speed.
- **Honest limits:** unmeasured confounding (agents reading urgency the score misses) and reverse causality cannot be excluded with observational data; adjustment is only fair for observed variables. Hence the **A/B test proposal** (evening/weekend on-call coverage, randomised by lead or day, primary metric conversion within 30 days, decision rule fixed in advance).
- **Error I caught while checking every number:** the first draft said the test would need "about 10 weeks"; with ~5 400 leads per arm and only ~11 300 out-of-hours leads a year it would take about a year. Rewritten with the trade-off made explicit (+3 pp needs ~2 500 per arm ≈ 5 months), verified with the power calculation.
- Checked against ARCHITECTURE §6.4: hypotheses pre-registered ✔, effect sizes + CIs ✔, statistical vs practical significance ✔, assumptions checked ✔, multiple comparisons corrected ✔, association vs causation with DAG and limitations ✔, estimates compared with the truth only after estimation ✔.
