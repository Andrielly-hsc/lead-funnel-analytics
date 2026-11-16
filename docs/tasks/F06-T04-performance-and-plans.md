# F06-T04 — Analyse execution plans and performance

| Field | Value |
|---|---|
| **Feature** | [F06 — Analytical SQL](../features/F06-analytical-sql.md) |
| **Status** | Done |
| **Estimate** | 2 h |
| **Depends on** | F06-T03 |
| **Branch** | `feat/F06-T04-performance-and-plans` |

## Description

Read plans and measure the effect of physical design choices.

## Steps

1. `EXPLAIN ANALYZE` on a heavy query; annotate operators (scan, hash join, aggregate)
2. Compare: query on CSV vs on table vs on Parquet partitioned by month (`read_parquet(..., hive_partitioning=true)`)
3. Explain DuckDB zone maps vs B-tree indexes in row stores (PostgreSQL) — when indexes help OLTP vs OLAP
4. Record timings in a table

## Acceptance criteria

- [ ] Plan annotated
- [ ] Timing comparison table with ≥ 3 variants

## Deliverables

- `docs/performance.md`
- `sql/analysis/06_performance.sql`

## Why this matters (best practice)

Column stores (DuckDB, Fabric, BigQuery) rely on partition pruning and min/max statistics more than on indexes. Knowing *why* shows architecture understanding.

## Notes

- `scripts/benchmark_sql.py` → `docs/performance.md` (generated). The warehouse is too small for meaningful timings, so the script builds a **scaled copy (5.15 M leads, 100×)** under `data/benchmark/` (git-ignored) and compares: CSV vs DuckDB table vs Parquet vs Parquet partitioned by month; sorted vs shuffled table (zone maps); full scan vs ART index for a point lookup. Medians of 9 runs after a warm-up; each (source, query) measured once and reused wherever it is reported.
- Typical results on this laptop: CSV ~300-500 ms and 281 MB vs Parquet ~10 ms and 30 MB; zone maps ~3× faster on date-sorted data; point lookup ~38 ms → ~2 ms with an ART index. The doc explains why column stores rely on compression, zone maps and partitioning rather than indexes, and when indexes matter (OLTP, point lookups, key enforcement).
- **Evidence over claims:** a first run showed *no* time gain from partition pruning, contradicting the text. The plan proved pruning works (`Scanning Files: 1/13`); at this size the fixed cost of listing/opening files is of the same order as the work, so the gain varies between runs. The report now shows the plan evidence and words the timing neutrally, instead of asserting a speed-up the numbers do not consistently show.
- **Readable execution plans:** DuckDB 2.0's default `EXPLAIN ANALYZE` renders boxes several hundred characters wide. The script parses `EXPLAIN (ANALYZE, FORMAT JSON)` into a compact tree with actual rows, **estimated rows**, operator time and key details (filters pushed into scans, join conditions). Estimates were ~9× too low on the joins — a talking point about why optimisers need good statistics.
- The plan is captured after a warm-up run; operator times are measured *while profiling* (overhead), and the doc reports the unprofiled time (~13 ms) next to it.
- Deviation: the planned `sql/analysis/06_performance.sql` became a Python script, because timing needs repeated runs, a scaled dataset and plan parsing, which plain SQL files run by `run_sql.py` cannot do.
- Recurring mistake of mine this feature: generating Python code through scripts turned `"\n"` into real line breaks three times; lint caught it each time. Code containing escapes is now edited directly.
