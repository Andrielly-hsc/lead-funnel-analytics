# ADR-0004: Use synthetic data with a known ground truth

- **Status:** Accepted
- **Date:** 2026-11-15

## Context

Public lead datasets are small, lack timestamps for response time, or have unclear licences. Real CRM data contains personal data and cannot be published.

## Decision

Generate **synthetic data** from an explicit causal model with documented parameters and injected quality issues.

## Consequences

- + No privacy or licence risk; fully publishable
- + Known true effects allow measuring estimator bias and detection accuracy — impossible with real data
- + Volume and issue rates are configurable
- − Results depend on generator assumptions → documented openly and tested with sensitivity analysis
- − Reviewers may see it as less 'real' → mitigated by realistic issues and an honest data card
