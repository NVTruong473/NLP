from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass
class RetrievalMetrics:
    hit_at_k: float
    precision_at_k: float
    recall_at_k: float
    mrr: float
    ndcg_at_k: float


def dcg(relevances: Sequence[int]) -> float:
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))


def retrieval_metrics(
    retrieved: Sequence[str],
    relevant: set[str],
    k: int = 5,
) -> RetrievalMetrics:
    top = list(retrieved[:k])
    rels = [1 if x in relevant else 0 for x in top]
    hit = 1.0 if any(rels) else 0.0
    precision = sum(rels) / k if k else 0.0
    recall = sum(rels) / len(relevant) if relevant else 0.0

    rr = 0.0
    for i, x in enumerate(retrieved, start=1):
        if x in relevant:
            rr = 1.0 / i
            break

    ideal = [1] * min(len(relevant), k)
    idcg = dcg(ideal)
    ndcg = dcg(rels) / idcg if idcg else 0.0
    return RetrievalMetrics(hit, precision, recall, rr, ndcg)


def average_metrics(rows: Iterable[RetrievalMetrics]) -> RetrievalMetrics:
    rows = list(rows)
    if not rows:
        return RetrievalMetrics(0, 0, 0, 0, 0)
    n = len(rows)
    return RetrievalMetrics(
        sum(r.hit_at_k for r in rows) / n,
        sum(r.precision_at_k for r in rows) / n,
        sum(r.recall_at_k for r in rows) / n,
        sum(r.mrr for r in rows) / n,
        sum(r.ndcg_at_k for r in rows) / n,
    )
