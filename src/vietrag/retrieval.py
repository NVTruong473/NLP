from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from .chunking import Chunk
from .providers import GeminiProvider, OpenRouterProvider, ProviderError


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[int]],
    weights: Sequence[float] | None = None,
    rrf_k: int = 60,
) -> dict[int, float]:
    weights = list(weights or [1.0] * len(rankings))
    scores: dict[int, float] = {}
    for ranking, weight in zip(rankings, weights):
        for rank, idx in enumerate(ranking, start=1):
            scores[idx] = scores.get(idx, 0.0) + weight / (rrf_k + rank)
    return scores


@dataclass
class RetrievedChunk:
    chunk: Chunk
    fused_score: float
    dense_score: float | None = None
    rerank_score: float | None = None


def source_diverse(
    results: Sequence[RetrievedChunk],
    *,
    max_per_source: int,
    limit: int | None = None,
) -> list[RetrievedChunk]:
    """Preserve ranking order while limiting repeated chunks from one source.

    This borrows the *multi-view retrieval* motivation from LightRAG without
    introducing an LLM-generated knowledge graph. It is especially useful for
    VB2CA questions that require evidence from both central regulations and a
    specific academy/school.
    """
    if max_per_source <= 0:
        return list(results[:limit] if limit is not None else results)

    counts: dict[str, int] = {}
    output: list[RetrievedChunk] = []
    for item in results:
        source = item.chunk.source or "__unknown__"
        if counts.get(source, 0) >= max_per_source:
            continue
        counts[source] = counts.get(source, 0) + 1
        output.append(item)
        if limit is not None and len(output) >= limit:
            break
    return output


class HybridIndex:
    def __init__(self, chunks: list[Chunk], index: faiss.Index, embedder: GeminiProvider):
        if not chunks:
            raise ValueError("HybridIndex requires at least one chunk")
        self.chunks = chunks
        self.index = index
        self.embedder = embedder
        self.bm25 = BM25Okapi([tokenize(c.text) for c in chunks])

    @classmethod
    def build(cls, chunks: list[Chunk], embedder: GeminiProvider, dimensions: int = 768):
        if not chunks:
            raise ValueError("Cannot build an index from zero chunks")
        vectors = np.asarray(
            embedder.embed_documents([c.text for c in chunks], dimensions=dimensions),
            dtype="float32",
        )
        if vectors.ndim != 2 or len(vectors) != len(chunks):
            raise ValueError("Embedding response shape does not match the number of chunks")
        faiss.normalize_L2(vectors)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(chunks=chunks, index=index, embedder=embedder)

    def save(self, directory: str | Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / "faiss.index"))
        with open(directory / "chunks.jsonl", "w", encoding="utf-8") as f:
            for c in self.chunks:
                f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")

    @classmethod
    def load(cls, directory: str | Path, embedder: GeminiProvider):
        directory = Path(directory)
        index_path = directory / "faiss.index"
        chunks_path = directory / "chunks.jsonl"
        if not index_path.exists() or not chunks_path.exists():
            raise FileNotFoundError(
                f"Missing index artifacts under {directory}. Run scripts/build_index.py first."
            )
        index = faiss.read_index(str(index_path))
        chunks: list[Chunk] = []
        with open(chunks_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(Chunk(**json.loads(line)))
        if index.ntotal != len(chunks):
            raise ValueError("FAISS index and chunk metadata are out of sync")
        return cls(chunks=chunks, index=index, embedder=embedder)

    def search(
        self,
        query: str,
        dense_top_k: int = 20,
        bm25_top_k: int = 20,
        fusion_top_k: int = 20,
        rrf_k: int = 60,
        dense_weight: float = 1.0,
        bm25_weight: float = 0.8,
        max_chunks_per_source: int = 3,
        reranker: OpenRouterProvider | None = None,
        rerank_top_k: int = 5,
    ) -> tuple[list[RetrievedChunk], float]:
        if not query.strip():
            return [], -1.0

        q = np.asarray([self.embedder.embed_query(query)], dtype="float32")
        faiss.normalize_L2(q)
        dense_scores, dense_ids = self.index.search(q, min(dense_top_k, len(self.chunks)))
        dense_ranking = [int(i) for i in dense_ids[0] if i >= 0]
        dense_map = {
            int(i): float(s)
            for i, s in zip(dense_ids[0], dense_scores[0])
            if i >= 0
        }

        bm25_scores = self.bm25.get_scores(tokenize(query))
        bm25_ranking = np.argsort(bm25_scores)[::-1][
            : min(bm25_top_k, len(self.chunks))
        ].tolist()

        fused = reciprocal_rank_fusion(
            [dense_ranking, bm25_ranking],
            weights=[dense_weight, bm25_weight],
            rrf_k=rrf_k,
        )
        fused_ids = sorted(fused, key=fused.get, reverse=True)
        results = [
            RetrievedChunk(
                chunk=self.chunks[idx],
                fused_score=float(fused[idx]),
                dense_score=dense_map.get(idx),
            )
            for idx in fused_ids
        ]

        # Keep broad evidence coverage before the second-stage reranker. This
        # prevents one very long source from occupying the entire candidate set.
        results = source_diverse(
            results,
            max_per_source=max_chunks_per_source,
            limit=fusion_top_k,
        )

        if reranker and results:
            try:
                reranked = reranker.rerank(
                    query,
                    [r.chunk.text for r in results],
                    top_n=min(rerank_top_k, len(results)),
                )
                new_results: list[RetrievedChunk] = []
                for item in reranked:
                    idx = int(item["index"])
                    if not 0 <= idx < len(results):
                        continue
                    original = results[idx]
                    original.rerank_score = float(item.get("relevance_score", 0.0))
                    new_results.append(original)
                if new_results:
                    results = new_results
                else:
                    results = results[:rerank_top_k]
            except (ProviderError, KeyError, TypeError, ValueError, IndexError):
                # Reranking is an optimization, not a single point of failure.
                results = results[:rerank_top_k]
        else:
            results = results[:rerank_top_k]

        top_dense = max(dense_map.values()) if dense_map else -1.0
        return results, top_dense
