# Lead Funnel Analytics

> Does a faster first response really increase lead conversion — and by how much?
> An end-to-end analytics case: synthetic CRM data → tested star schema (dbt + DuckDB) →
> rigorous statistical inference → KPI dashboard.

[![CI](https://github.com/Andrielly-hsc/lead-funnel-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/Andrielly-hsc/lead-funnel-analytics/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Status:** 🚧 in development — see the [backlog](docs/README.md).

## Challenge

_To be written when results are available (F10-T01)._

## Solution

_See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the planned architecture._

## Result

_To be written._

## Getting started

Requirements: Python 3.11+, Git.

```bash
git clone https://github.com/Andrielly-hsc/lead-funnel-analytics.git
cd lead-funnel-analytics
py -3.11 -m venv .venv                 # macOS/Linux: python3.11 -m venv .venv
.venv\Scriptsctivate                 # macOS/Linux: source .venv/bin/activate
pip install -r requirements-lock.txt   # exact, pinned versions
pip install -e . --no-deps             # the package itself, in editable mode
lead-funnel --version
```

### Generate the synthetic data

```bash
lead-funnel generate --seed 42            # 50 000 leads -> data/raw/
lead-funnel generate --n-leads 2000 --clean  # small, clean sample
```

The same seed always produces byte-identical files (see `data/raw/_manifest.json`).

### Load the raw layer

```bash
lead-funnel ingest                 # data/raw/ -> data/warehouse/lead_funnel.duckdb (schema raw)
lead-funnel ingest                 # again: unchanged files are skipped (idempotent)
lead-funnel ingest --full-refresh  # reload everything
```

Files that break the data contract are moved to `data/quarantine/`; every decision is
recorded in `meta.load_log`.

### Build the star schema (dbt)

```bash
dbt deps  --project-dir dbt --profiles-dir dbt   # install dbt_utils (once)
dbt build --project-dir dbt --profiles-dir dbt   # seeds, staging, intermediate, marts + data tests
dbt docs generate --project-dir dbt --profiles-dir dbt && dbt docs serve --project-dir dbt --profiles-dir dbt
```

Lineage diagram: [docs/lineage.md](docs/lineage.md).

<details>
<summary>Windows: folder path with accents (e.g. <code>Portifólio</code>)</summary>

Python 3.11 on Windows reads the editable-install <code>.pth</code> file with the
legacy code page, so a non-ASCII folder path breaks <code>import lead_funnel</code>.
Clone into an ASCII-only path, or set <code>PYTHONUTF8=1</code> in your environment.
</details>

### Updating dependencies

Edit the ranges in `pyproject.toml`, then regenerate the lock file:

```bash
pip-compile --extra dev --strip-extras --no-emit-index-url -o requirements-lock.txt pyproject.toml
```

## Project documentation

| Document | Purpose |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | System design and engineering conventions |
| [Decision records](docs/adr/) | Why key technical choices were made |
| [Backlog](docs/README.md) | Features and tasks, with status |

## License

[MIT](LICENSE)
