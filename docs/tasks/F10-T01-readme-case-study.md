# F10-T01 — Write the README as a case study

| Field | Value |
|---|---|
| **Feature** | [F10 — Case study documentation & release](../features/F10-case-study-and-release.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | — |
| **Branch** | `feat/F10-T01-readme-case-study` |

## Description

Mirror the structure iSYS uses for its own project cases.

## Steps

1. Sections: Challenge · Solution · Result · Architecture (diagram) · How to run · Repository map · What I learned
2. Key numbers: SLA lift (adjusted, with CI), naïve bias, data-quality score
3. Badges: CI, Python version, licence

## Acceptance criteria

- [ ] A non-technical reader understands the result from the first screen

## Deliverables

- `README.md`

## Why this matters (best practice)

Recruiters spend under a minute per repo. Leading with business impact — not with installation steps — is what makes a portfolio *attractive*.

## Notes

- README rewritten as a **case study** in the structure iSYS uses for its own project pages: Challenge → Solution → Result, with the three key numbers and the hero figure (naïve vs adjusted vs true effect) on the first screen, before any installation step. Recruiters read the result; engineers follow the links.
- Sections: key-number table, Challenge (three questions), Solution (pipeline diagram + one row per feature with its highlight), Result (four findings with their evidence links), Run it (the whole pipeline in ~12 commands), Repository map, What I learned, licence. The synthetic nature of the data is stated right under the hero figure, with a link to ADR-0004.
- Every number was checked against the generated reports before committing. Two of my draft errors were corrected: the dbt test count had grown from 105 (F04) to **120** (F05 added tests); and "merged 6 304 different people" was wrong — 6 304 is the number of false *pairs*.
- Fixed a bug present since F01: the activation command read `.venv\Scriptsctivate` because `\a` had been turned into a control character when the README was edited through a Python string.
- Added badges for dbt and DuckDB versions next to CI, Python and licence.
