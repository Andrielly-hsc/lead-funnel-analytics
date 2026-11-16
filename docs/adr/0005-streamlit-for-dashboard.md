# ADR-0005: Use Streamlit for the dashboard (Power BI optional)

- **Status:** Accepted
- **Date:** 2026-11-15

## Context

The dashboard must be runnable by any reviewer from the repo. Power BI is common in the Microsoft ecosystem (relevant for iSYS) but needs Windows + Power BI Desktop and `.pbix` files are binary (bad for code review).

## Decision

Build the primary dashboard in **Streamlit**; offer a Power BI version as an optional task (F09-T04) reusing the same star schema.

## Consequences

- + Pure Python, versionable, runs anywhere
- + Same marts serve both tools, demonstrating good dimensional design
- − Streamlit is less common than Power BI in enterprise BI
