"""Near-duplicate detection: compare matching strategies against the ground truth.

Record linkage always trades two errors:

* **false match** (two different people merged) — wrong attribution, and possibly one
  customer's data shown to another (GDPR accuracy and confidentiality);
* **missed match** (one person kept twice) — double counting and double contact.

With real data the true pairs are unknown, so precision and recall can only be
estimated from a hand-labelled sample. Here the generator logged every injected
near-duplicate pair, so both can be measured exactly for each strategy.

Strategies use *blocking* (only records sharing a key are compared) so that we never
score all n² pairs.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import resources

import duckdb
import pandas as pd
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

Pair = tuple[str, str]

LEGAL_SUFFIXES = re.compile(
    r"\b(gmbh & co\. kg|gmbh|ag|b\.v\.|n\.v\.|bv|sa|sas|sarl|s\.r\.l\.|s\.p\.a\.|s\.l\.|s\.a\.|"
    r"sp\. z o\.o\.|aps|a/s)$"
)


@dataclass(frozen=True)
class Evaluation:
    strategy: str
    predicted: int
    true_positives: int
    precision: float
    recall: float

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    @property
    def false_matches(self) -> int:
        return self.predicted - self.true_positives


def normalise_company(name: pd.Series) -> pd.Series:
    """Lower-case, drop the legal suffix and punctuation: 'Flagal S.L.' -> 'flagal'."""
    s = name.str.lower().str.strip().str.replace(LEGAL_SUFFIXES, "", regex=True)
    return s.str.replace(r"[^a-z0-9 ]", "", regex=True).str.strip()


def normalise_phone(phone: pd.Series) -> pd.Series:
    return phone.str.replace(r"\D", "", regex=True).str.replace(r"^00", "", regex=True)


def load_leads(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Unique raw leads (exact duplicates removed) with the standardised country."""
    return con.execute(
        """
        select r.lead_id, r.email, r.phone, r.company_name, s.country_code, r.created_at
        from (select distinct * exclude (_loaded_at, _source_file, _file_hash, _run_id)
              from raw.leads) r
        join staging.stg_crm__leads s using (lead_id)
        """
    ).df()


def _pairs_sharing(df: pd.DataFrame, key: pd.Series) -> set[Pair]:
    """All (earlier, later) lead pairs that share a non-null blocking key."""
    keyed = df.assign(_k=key.to_numpy()).dropna(subset=["_k"])
    keyed = keyed[keyed.duplicated("_k", keep=False)]
    pairs: set[Pair] = set()
    for _, group in keyed.sort_values(["created_at", "lead_id"]).groupby("_k"):
        ids = group["lead_id"].tolist()
        pairs.update((ids[i], ids[j]) for i in range(len(ids)) for j in range(i + 1, len(ids)))
    return pairs


def exact_email(df: pd.DataFrame) -> set[Pair]:
    """E-mail compared exactly as typed (case-sensitive)."""
    return _pairs_sharing(df, df["email"])


def normalised_email(df: pd.DataFrame) -> set[Pair]:
    return _pairs_sharing(df, df["email"].str.lower().str.strip())


def normalised_phone(df: pd.DataFrame) -> set[Pair]:
    return _pairs_sharing(df, normalise_phone(df["phone"]))


def email_or_phone(df: pd.DataFrame) -> set[Pair]:
    """The deterministic rule used in dbt (int_leads__duplicates)."""
    return normalised_email(df) | normalised_phone(df)


def fuzzy_company_candidates(df: pd.DataFrame, max_days: float = 14.0) -> pd.DataFrame:
    """Candidate pairs blocked on country + first 3 letters of the normalised company name,
    created at most ``max_days`` apart, scored with ``token_sort_ratio`` (0-100).

    The self-join runs in DuckDB: the date condition is applied *during* the join, so the
    ~12 million same-block pairs are never materialised (a pandas merge took ~60 s).
    """
    d = df.assign(company=normalise_company(df["company_name"]))
    d["block"] = d["country_code"] + ":" + d["company"].str[:3]
    with duckdb.connect() as con:
        con.register("d", d[["lead_id", "company", "block", "created_at"]])
        cand = con.execute(
            """
            select
                case when a.created_at <= b.created_at then a.lead_id else b.lead_id end as a,
                case when a.created_at <= b.created_at then b.lead_id else a.lead_id end as b,
                a.company as company_a,
                b.company as company_b
            from d a
            join d b
                on a.block = b.block
                and a.lead_id < b.lead_id
                and abs(epoch(a.created_at) - epoch(b.created_at)) <= ? * 86400
            """,
            [max_days],
        ).df()
    cand["score"] = [
        fuzz.token_sort_ratio(x, y)
        for x, y in zip(cand["company_a"], cand["company_b"], strict=True)
    ]
    return cand[["a", "b", "score"]]


def evaluate(name: str, predicted: Iterable[Pair], truth: set[Pair]) -> Evaluation:
    pred = {tuple(sorted(p)) for p in predicted}
    true = {tuple(sorted(p)) for p in truth}
    tp = len(pred & true)
    return Evaluation(
        strategy=name,
        predicted=len(pred),
        true_positives=tp,
        precision=tp / len(pred) if pred else 0.0,
        recall=tp / len(true) if true else 0.0,
    )


def compare_strategies(
    df: pd.DataFrame, truth: set[Pair], fuzzy_thresholds: Iterable[int] = (80, 90, 95, 100)
) -> pd.DataFrame:
    results = [
        evaluate("exact e-mail (as typed)", exact_email(df), truth),
        evaluate("normalised e-mail", normalised_email(df), truth),
        evaluate("normalised phone", normalised_phone(df), truth),
        evaluate("normalised e-mail OR phone (chosen)", email_or_phone(df), truth),
    ]
    candidates = fuzzy_company_candidates(df)
    for t in fuzzy_thresholds:
        above = candidates[candidates["score"] >= t]
        results.append(
            evaluate(
                f"fuzzy company name ≥ {t} (same country, ≤ 14 days)",
                zip(above["a"], above["b"], strict=True),
                truth,
            )
        )
    table = pd.DataFrame(
        [
            {
                "strategy": r.strategy,
                "predicted_pairs": r.predicted,
                "true_matches": r.true_positives,
                "false_matches": r.false_matches,
                "precision": r.precision,
                "recall": r.recall,
                "f1": r.f1,
            }
            for r in results
        ]
    )
    logger.info("Compared %d matching strategies", len(table))
    return table


def to_markdown(table: pd.DataFrame, n_truth: int) -> str:
    """Render the report from the template ``templates/dedup_report.md``."""
    rows = [
        f"| {r.strategy} | {r.predicted_pairs:,} | {r.true_matches:,} | {r.false_matches:,} | "
        f"{r.precision:.3f} | {r.recall:.3f} | {r.f1:.3f} |"
        for r in table.itertuples(index=False)
    ]
    chosen = table[table["strategy"].str.contains("chosen")].iloc[0]
    exact = table[table["strategy"].str.startswith("exact")].iloc[0]
    template = resources.files("lead_funnel.quality").joinpath("templates/dedup_report.md")
    return template.read_text(encoding="utf-8").format(
        n_truth=n_truth,
        rows="\n".join(rows),
        chosen_p=f"{chosen['precision']:.3f}",
        chosen_r=f"{chosen['recall']:.3f}",
        exact_r=f"{exact['recall']:.0%}",
    )
