# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repository structure, licence and planning documentation (architecture, ADRs, backlog).
- Python packaging (`pyproject.toml`, `src/` layout) with a pinned lock file.
- Code quality tooling: ruff, sqlfluff and pre-commit hooks.
- pytest scaffolding with branch coverage and a temporary DuckDB fixture.
- GitHub Actions CI (lint + tests on Ubuntu and Windows) and pull request template.
- Configuration from environment variables / `.env`, logging setup and the `lead-funnel` CLI skeleton.
- Synthetic CRM generator (`lead-funnel generate`): data contract, causal model with a known effect of
  response time on conversion, realistic data-quality issues, CSV/JSONL/Parquet landing zone with
  ground truth and manifest.
- Ingestion into the DuckDB raw layer (`lead-funnel ingest`): explicit types from the data contract,
  snapshot replace in one transaction, idempotent by file hash, quarantine of contract violations and
  an audit trail in `meta.load_log`.
- dbt star schema on DuckDB: staging (standardisation seeds, pseudonymisation), intermediate
  (single SLA definition), marts (`fct_leads`, `fct_interactions`, conformed dimensions, SCD2
  `dim_agent` with point-in-time joins), reconciliation tests, exposures and generated lineage;
  end-to-end pipeline job in CI.
- Data quality (`lead-funnel profile`): exact column profiles, a 16-metric scorecard over the six
  quality dimensions (raw vs after the pipeline, accuracy against the ground truth), error/warn
  dbt tests with a known-issues register, and near-duplicate flagging justified by a
  precision/recall comparison of matching strategies.
- Analytical SQL (`sql/analysis/`, results in `reports/sql/`): funnel and SLA KPIs, window functions,
  cohorts, nine reproduced SQL pitfalls (`docs/sql_pitfalls.md`) and a performance benchmark of
  formats, partitioning, zone maps and indexes with an annotated execution plan
  (`docs/performance.md`).
