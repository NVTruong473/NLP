from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from vietrag.config import load_config
from vietrag.providers import GeminiProvider
from vietrag.retrieval import HybridIndex
from vietrag.secrets import load_provider_env


def balanced_accuracy(labels, predictions):
    tp = sum(1 for y, p in zip(labels, predictions) if y == 1 and p == 1)
    tn = sum(1 for y, p in zip(labels, predictions) if y == 0 and p == 0)
    pos = sum(labels)
    neg = len(labels) - pos
    tpr = tp / pos if pos else 0.0
    tnr = tn / neg if neg else 0.0
    return (tpr + tnr) / 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--dataset", default="evaluation/sample_eval.jsonl")
    parser.add_argument("--env", default="/content/providers.env")
    args = parser.parse_args()

    load_provider_env(args.env)
    cfg = load_config(args.config)
    gemini = GeminiProvider()
    index = HybridIndex.load(cfg.index_dir, gemini)
    rows = [
        json.loads(x)
        for x in Path(args.dataset).read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    if not rows:
        raise SystemExit("Calibration dataset is empty.")

    labels = []  # 1 = in-domain / answerable; 0 = OOD
    scores = []
    for row in rows:
        _, top_dense = index.search(
            row["question"],
            dense_top_k=5,
            bm25_top_k=5,
            fusion_top_k=5,
            rerank_top_k=5,
        )
        labels.append(0 if row.get("ood") else 1)
        scores.append(top_dense)

    if len(set(labels)) < 2:
        raise SystemExit("Calibration needs both in-domain and OOD examples.")

    candidates = sorted(
        set(np.linspace(min(scores) - 1e-6, max(scores) + 1e-6, 101).tolist())
    )
    best = max(
        (
            (balanced_accuracy(labels, [int(s >= t) for s in scores]), t)
            for t in candidates
        ),
        key=lambda x: x[0],
    )
    print(f"Recommended ood_dense_threshold: {best[1]:.4f}")
    print(f"Balanced accuracy on calibration set: {best[0]:.4f}")
    print(
        "Use a larger held-out dataset before treating this threshold as production-ready."
    )


if __name__ == "__main__":
    main()
