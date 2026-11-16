# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-11-15

## Context

Decisions about tools and structure are easy to forget and hard to explain later ("why DuckDB and not Postgres?").

## Decision

We record every significant decision as an ADR in `docs/adr/`, using the Michael Nygard format: Context, Decision, Consequences. ADRs are immutable; a changed decision gets a new ADR that *supersedes* the old one.

## Consequences

- + Reviewers see the reasoning, not just the result
- + Forces explicit trade-off thinking
- − Small overhead per decision
