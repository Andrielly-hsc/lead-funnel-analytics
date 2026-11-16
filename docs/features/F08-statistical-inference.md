# F08 — Statistical inference & relationships

| Field | Value |
|---|---|
| **Status** | In Progress |
| **Priority** | Must (MoSCoW) |
| **Depends on** | [F07](F07-exploratory-analysis.md) |
| **Estimate** | 12 h |
| **Created** | 2026-11-15 |

## Goal

Test the response-time hypothesis rigorously, quantify relationships, and distinguish association from causation.

## User story

> As a decision maker, I want to know whether investing in faster responses is likely to increase conversions, and by how much, with honest uncertainty.

## Scope

**In scope**

- Analysis plan (pre-registration)
- Proportion tests, CIs, bootstrap, power
- Correlation and ANOVA
- Logistic regression with confounder adjustment
- Causal reasoning and limitations
- Multiple testing and robustness

**Out of scope**

- Advanced causal ML (double ML, causal forests) — mentioned as future work

## Acceptance criteria

- [ ] Analysis plan committed *before* inference results (visible in git history)
- [ ] Every result: estimate, 95 % CI, p-value, effect size, practical interpretation
- [ ] Naïve vs adjusted vs true effect compared in one table

## Tasks

| ID | Task | Estimate | Status |
|---|---|---|---|
| [F08-T01](../tasks/F08-T01-analysis-plan.md) | Write the analysis plan (pre-registration) | 1 h | Done |
| [F08-T02](../tasks/F08-T02-proportion-tests-and-ci.md) | Test conversion difference with CIs and effect sizes | 2 h | To Do |
| [F08-T03](../tasks/F08-T03-correlation-and-anova.md) | Analyse correlations and ANOVA | 2 h | To Do |
| [F08-T04](../tasks/F08-T04-logistic-regression-adjustment.md) | Estimate adjusted effect with logistic regression | 3 h | To Do |
| [F08-T05](../tasks/F08-T05-causality-and-limitations.md) | Write the causal reasoning and limitations section | 2 h | To Do |
| [F08-T06](../tasks/F08-T06-multiple-testing-robustness.md) | Correct for multiple testing and run robustness checks | 2 h | To Do |

## Syllabus topics covered

- 2.1 Probability, sampling, estimation, confidence intervals, hypothesis tests
- 2.2 Assumptions, uncertainty, inference errors; statistical significance and practical relevance
- 3.1 Correlation, regression, ANOVA; assumptions, effect size, interpretation
- 3.2 Association, prediction and causality; selection, representativeness, alternative explanations

## Definition of Done

- All tasks are **Done** and their acceptance criteria are met
- Code merged to `main` through a Pull Request with green CI
- Documentation (README / docs) updated
- [ARCHITECTURE.md](../ARCHITECTURE.md) conventions followed (or an ADR records the deviation)
