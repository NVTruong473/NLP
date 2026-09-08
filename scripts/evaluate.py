from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from vietrag.config import load_config
from vietrag.evaluation import average_metrics, retrieval_metrics
from vietrag.providers import GeminiProvider, OpenRouterProvider
from vietrag.retrieval import HybridIndex
from vietrag.secrets import load_provider_env


def safe_div(a: int, b: int) -> float | None:
    return a / b if b else None


def unique_in_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--dataset", default="evaluation/sample_eval.jsonl")
    parser.add_argument("--env", default="/content/providers.env")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    load_provider_env(args.env)
    cfg = load_config(args.config)
    gemini = GeminiProvider()
    openrouter = OpenRouterProvider()
    index = HybridIndex.load(cfg.index_dir, embedder=gemini)

    rows = [
        json.loads(x)
        for x in Path(args.dataset).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    metrics = []
    in_total = in_accepted = 0
    ood_total = ood_rejected = 0

    for row in rows:
        results, top_dense = index.search(
            row["question"],
            dense_top_k=cfg.retrieval.dense_top_k,
            bm25_top_k=cfg.retrieval.bm25_top_k,
            fusion_top_k=cfg.retrieval.fusion_top_k,
            rrf_k=cfg.retrieval.rrf_k,
            dense_weight=cfg.retrieval.dense_weight,
            bm25_weight=cfg.retrieval.bm25_weight,
            reranker=openrouter,
            rerank_top_k=max(args.k, cfg.retrieval.rerank_top_k),
        )
        # Evaluate document/source retrieval, not repeated chunks from the same source.
        retrieved_sources = unique_in_order([r.chunk.source for r in results])
        relevant = set(row.get("relevant_sources", []))
        if relevant:
            metrics.append(retrieval_metrics(retrieved_sources, relevant, k=args.k))

        predicted_in_domain = top_dense >= cfg.retrieval.ood_dense_threshold
        if row.get("ood"):
            ood_total += 1
            ood_rejected += int(not predicted_in_domain)
        else:
            in_total += 1
            in_accepted += int(predicted_in_domain)

    summary = asdict(average_metrics(metrics))
    in_acceptance = safe_div(in_accepted, in_total)
    ood_rejection = safe_div(ood_rejected, ood_total)
    summary["in_domain_acceptance_rate"] = in_acceptance
    summary["ood_rejection_rate"] = ood_rejection
    summary["ood_balanced_accuracy"] = (
        (in_acceptance + ood_rejection) / 2
        if in_acceptance is not None and ood_rejection is not None
        else None
    )
    summary["evaluated_questions"] = len(rows)
    summary["retrieval_questions"] = len(metrics)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
