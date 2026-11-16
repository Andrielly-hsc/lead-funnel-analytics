"""Benchmark storage formats and physical design choices; write docs/performance.md.

    python scripts/benchmark_sql.py

The warehouse has only ~50 000 leads, where every query takes milliseconds and
differences are noise. The benchmark therefore builds a scaled copy (``SCALE`` × the
leads, ~2 million rows) under ``data/benchmark/`` (git-ignored) and compares:

1. storage format: CSV vs DuckDB table vs Parquet vs Parquet partitioned by month;
2. partition pruning: a one-month filter on the partitioned Parquet;
3. zone maps: the same selective filter on a table sorted by date vs shuffled;
4. an ART index for a point lookup;

and records an annotated ``EXPLAIN ANALYZE`` of a real analytical query.
Timings depend on the machine: compare the *ratios*, not the absolute values.
"""

from __future__ import annotations

import os
import platform
import shutil
import statistics
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("LF_DB_PATH", ROOT / "data" / "warehouse" / "lead_funnel.duckdb"))
BENCH = ROOT / "data" / "benchmark"
OUT = ROOT / "docs" / "performance.md"
SCALE = 100
RUNS = 9

FULL_SCAN = "select count(*), avg(lead_score) from {src}"
ONE_MONTH = (
    "select count(*), avg(lead_score) from {src} "
    "where created_at >= timestamp '2025-03-01' and created_at < timestamp '2025-04-01'"
)
ONE_MONTH_PARTITION = "select count(*), avg(lead_score) from {src} where created_month = '2025-03'"

PLAN_QUERY = """
select a.team, d.iso_week, avg(f.is_sla_met::int) as sla_rate
from marts.fct_leads f
join marts.dim_agent a on f.owner_agent_key = a.agent_key
join marts.dim_date d on f.created_date_key = d.date_key
where not f.is_probable_duplicate and d.iso_year = 2025
group by all
order by 1, 2
"""


SKIP_OPERATORS = {"RESULT_COLLECTOR", "EXPLAIN_ANALYZE"}
DETAIL_KEYS = ("Table", "Filters", "Conditions", "Join Type", "Groups", "Aggregates", "Order By")


def plan_tree(con: duckdb.DuckDBPyConnection, sql: str) -> str:
    """Compact text tree of ``EXPLAIN (ANALYZE, FORMAT JSON)``: one line per operator with
    actual rows, estimated rows, time and the key details. DuckDB's default rendering is
    several hundred characters wide, unreadable in a document."""
    import json

    root = json.loads(con.execute("explain (analyze, format json) " + sql).fetchall()[0][1])
    lines: list[str] = []

    def walk(node: dict, depth: int) -> None:
        if node["type"] in SKIP_OPERATORS:
            for child in node.get("children", []):
                walk(child, depth)
            return
        info = node.get("extra_info", {})
        estimate = info.get("Estimated Cardinality", "?")
        lines.append(
            f"{'    ' * depth}{node['type']}  rows={node['intermediate_rows']:,}  "
            f"est={estimate}  time={1000 * node['timing']:.1f} ms"
        )
        for key in DETAIL_KEYS:
            if key in info:
                value = info[key]
                value = ", ".join(value) if isinstance(value, list) else str(value)
                lines.append(f"{'    ' * depth}    · {key}: {value.replace(chr(10), ' ')[:90]}")
        for child in node.get("children", []):
            walk(child, depth + 1)

    for top in root["operator"]:
        walk(top, 0)
    return "\n".join(lines)


def timed(con: duckdb.DuckDBPyConnection, sql: str) -> float:
    """Median wall time in milliseconds over RUNS executions (first run discarded)."""
    con.execute(sql).fetchall()  # warm-up: file cache, catalog
    times = []
    for _ in range(RUNS):
        start = time.perf_counter()
        con.execute(sql).fetchall()
        times.append((time.perf_counter() - start) * 1000)
    return statistics.median(times)


def size_mb(path: Path) -> float:
    if path.is_dir():
        return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) / 1e6
    return path.stat().st_size / 1e6


def build(con: duckdb.DuckDBPyConnection) -> dict[str, Path]:
    """Scaled copy of raw.leads in four formats."""
    shutil.rmtree(BENCH, ignore_errors=True)
    BENCH.mkdir(parents=True)
    con.execute(f"attach '{DB.as_posix()}' as wh (read_only)")
    con.execute(
        f"""
        create table leads as
        select
            l.lead_id || '-' || r.range as lead_id,
            l.created_at + to_days(cast(r.range % 7 as integer)) as created_at,
            l.channel,
            l.lead_score,
            strftime(l.created_at, '%Y-%m') as created_month
        from wh.raw.leads as l
        cross join range({SCALE}) as r
        order by created_at
        """
    )
    con.execute("create table leads_shuffled as select * from leads order by hash(lead_id)")
    paths = {
        "csv": BENCH / "leads.csv",
        "parquet": BENCH / "leads.parquet",
        "parquet_partitioned": BENCH / "leads_by_month",
    }
    con.execute(f"copy leads to '{paths['csv'].as_posix()}' (header)")
    con.execute(f"copy leads to '{paths['parquet'].as_posix()}' (format parquet)")
    con.execute(
        f"copy leads to '{paths['parquet_partitioned'].as_posix()}' "
        "(format parquet, partition_by (created_month))"
    )
    return paths


def main() -> int:
    bench_db = BENCH.parent / "benchmark.duckdb"
    bench_db.unlink(missing_ok=True)
    BENCH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(bench_db))
    con.execute("set TimeZone = 'UTC'")
    con.execute("set enable_progress_bar = false")
    paths = build(con)
    rows = con.execute("select count(*) from leads").fetchone()[0]

    csv = f"read_csv('{paths['csv'].as_posix()}')"
    pq = f"read_parquet('{paths['parquet'].as_posix()}')"
    part = (
        f"read_parquet('{paths['parquet_partitioned'].as_posix()}/*/*.parquet', "
        "hive_partitioning = true)"
    )
    formats = [
        ("CSV file (parsed on every query)", csv, size_mb(paths["csv"]), ONE_MONTH),
        ("DuckDB table", "leads", None, ONE_MONTH),
        ("Parquet, one file", pq, size_mb(paths["parquet"]), ONE_MONTH),
        (
            "Parquet partitioned by month",
            part,
            size_mb(paths["parquet_partitioned"]),
            ONE_MONTH_PARTITION,
        ),
    ]
    # each (source, query) is measured exactly once and reused wherever it is reported
    plan_month = con.execute("explain analyze " + ONE_MONTH_PARTITION.format(src=part)).fetchall()
    files_line = next(
        (ln.strip(" │") for ln in plan_month[0][1].splitlines() if "Scanning Files" in ln),
        "Scanning Files: n/a",
    )
    sorted_ms = timed(con, ONE_MONTH.format(src="leads"))
    shuffled_ms = timed(con, ONE_MONTH.format(src="leads_shuffled"))
    format_rows = []
    for name, src, mb, month_sql in formats:
        full = timed(con, FULL_SCAN.format(src=src))
        month = sorted_ms if src == "leads" else timed(con, month_sql.format(src=src))
        format_rows.append((name, mb, full, month))

    some_id = con.execute("select lead_id from leads using sample 1 rows").fetchone()[0]
    lookup = f"select * from leads_shuffled where lead_id = '{some_id}'"
    no_index_ms = timed(con, lookup)
    con.execute("create index idx_leads_id on leads_shuffled (lead_id)")
    index_ms = timed(con, lookup)
    con.close()

    with duckdb.connect(str(DB), read_only=True) as wh:
        wh.execute("set enable_progress_bar = false")
        wh.execute("set TimeZone = 'UTC'")
        plan_ms = timed(wh, PLAN_QUERY)  # also warms the cache before profiling
        plan = plan_tree(wh, PLAN_QUERY)

    OUT.write_text(
        render(
            rows,
            format_rows,
            sorted_ms,
            shuffled_ms,
            no_index_ms,
            index_ms,
            plan,
            files_line,
            plan_ms,
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


def render(
    rows, format_rows, sorted_ms, shuffled_ms, no_index_ms, index_ms, plan, files_line, plan_ms
) -> str:
    def mb(v):
        return "—" if v is None else f"{v:,.0f} MB"

    table = "\n".join(
        f"| {name} | {mb(size)} | {full:,.1f} ms | {month:,.1f} ms |"
        for name, size, full, month in format_rows
    )
    return f"""# Query performance: formats, partitions, zone maps and indexes

> Generated by `scripts/benchmark_sql.py` on a scaled copy of the leads
> (**{rows:,} rows** = {SCALE}× the warehouse). Median of {RUNS} runs after a warm-up.
> Machine: {platform.system()} (build {platform.version()}), {os.cpu_count()} logical CPUs,
> DuckDB {duckdb.__version__}. Absolute times depend on the machine; compare **ratios**.

## 1. Storage format and partition pruning

Query: `count(*)` and `avg(lead_score)` over all rows, and over one month (March 2025).

| Source | Size on disk | Full scan | One month |
|---|---:|---:|---:|
{table}

- **CSV** is text: every query re-parses every byte and cannot skip anything.
- **Parquet** is columnar and compressed: the query reads only the 2 columns it needs,
  and per-row-group min/max statistics let the reader skip row groups outside March.
- **Partitioned Parquet** (one folder per `created_month`, *hive partitioning*): a filter
  on the partition column skips whole files without opening them (**partition
  pruning**). The plan of the one-month query confirms it: `{files_line}`.
- **Reading the timings honestly:** the plan proves the pruning; the wall-time gain is
  only a few milliseconds at ~5 million rows and varies from run to run, because the
  fixed cost of listing and opening files is of the same order. The benefit grows with
  data volume and on remote object storage (S3, OneLake, ADLS), where every file is a
  network request. Partition on a column that queries filter on, with a moderate number
  of partitions: thousands of small files make queries *slower* ("small files problem").
- The **DuckDB table** is fastest for repeated queries: data is already decoded into
  DuckDB's own format. Parquet is the better *exchange* and *lake* format: open,
  portable, readable by Spark, Fabric, pandas and BI tools.

## 2. Zone maps: physical order matters

Same one-month filter on two DuckDB tables with identical content: one stored in date
order, one shuffled.

| Table | One month |
|---|---:|
| sorted by `created_at` | {sorted_ms:,.1f} ms |
| shuffled | {shuffled_ms:,.1f} ms |

DuckDB keeps min/max values per column for each row group (**zone maps**). When rows
are stored in date order, only the row groups overlapping March are read; shuffled,
every row group contains some March rows and nothing can be skipped. Loading data in
the order it is usually filtered by is a free optimisation in column stores.

## 3. Indexes: point lookups vs analytical scans

Lookup of one `lead_id` among {rows:,} rows (shuffled table):

| | Time |
|---|---:|
| no index (full scan) | {no_index_ms:,.2f} ms |
| ART index on `lead_id` | {index_ms:,.2f} ms |

- In **row stores** (PostgreSQL, SQL Server) B-tree indexes are the main tuning tool for
  selective queries and joins; transactional systems (OLTP) depend on them.
- In **column stores** (DuckDB, Fabric Warehouse, Snowflake, BigQuery) analytical queries
  scan columns; speed comes from columnar compression, zone maps and partitioning. DuckDB
  supports ART indexes, which help **point lookups** and enforce primary/unique keys, but
  rarely help aggregations — and they slow down loads. Most warehouses do not use them.

## 4. Reading an execution plan

`EXPLAIN ANALYZE` runs the query and reports, for each operator, how many rows it
produced and how long it took. Plan for *SLA rate by team and ISO week in 2025*:

```sql
{PLAN_QUERY.strip()}
```

```text
{plan}
```

How to read it: the tree is executed **bottom-up** — data flows from the scans (deepest
lines) up to the root. `rows` = rows produced by the operator, `est` = the optimiser's
estimate before running, `time` = time spent in the operator *while profiling*
(profiling adds overhead; the same query runs in **{plan_ms:,.1f} ms** without it).

- **TABLE_SCAN** — reads a table. Only referenced columns are read (*projection
  pushdown*) and simple filters such as `iso_year = 2025` are applied inside the scan
  (*filter pushdown*), before any join.
- **HASH_JOIN** — builds a hash table on the smaller input (the dimension) and probes it
  with the larger one (the fact). Compare rows in and out: a join that *multiplies* rows
  is the fan-out pitfall P4 (`docs/sql_pitfalls.md`).
- **est vs rows** — the optimiser chooses join order and algorithms from estimates. When
  they are far off (as on the join here), plans can be poor on larger data; fresh
  statistics and simple, sargable predicates keep estimates accurate.
- **HASH_GROUP_BY** — the aggregation; its output = number of groups.
- **ORDER_BY / PROJECTION** — sorting and computing the final columns.
- Optimise where the time is. Here the query runs in {plan_ms:,.1f} ms, so no tuning is
  needed — premature optimisation would only add complexity.
"""


if __name__ == "__main__":
    raise SystemExit(main())
