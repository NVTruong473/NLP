from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RetrievalConfig:
    dense_top_k: int = 20
    bm25_top_k: int = 20
    fusion_top_k: int = 20
    rerank_top_k: int = 5
    rrf_k: int = 60
    dense_weight: float = 1.0
    bm25_weight: float = 0.8
    max_chunks_per_source: int = 3
    ood_dense_threshold: float = 0.28


@dataclass
class ChunkingConfig:
    chunk_words: int = 350
    overlap_words: int = 60
    min_chunk_words: int = 40


@dataclass
class GenerationConfig:
    provider_order: tuple[str, ...] = ("gemini", "openrouter")
    max_context_chars: int = 18000
    temperature: float | None = None


@dataclass
class AppConfig:
    index_dir: str = "artifacts/index"
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)


def _merge_dataclass(cls, values: dict[str, Any] | None):
    values = values or {}
    return cls(**{k: v for k, v in values.items() if k in cls.__dataclass_fields__})


def load_config(path: str | Path) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    generation = raw.get("generation") or {}
    if "provider_order" in generation:
        generation = dict(generation)
        generation["provider_order"] = tuple(generation["provider_order"])

    # Colab quick-resume can point at a persistent Google Drive cache without
    # editing the committed YAML file.
    index_dir = os.getenv("VIETRAG_INDEX_DIR", raw.get("index_dir", "artifacts/index"))

    return AppConfig(
        index_dir=index_dir,
        chunking=_merge_dataclass(ChunkingConfig, raw.get("chunking")),
        retrieval=_merge_dataclass(RetrievalConfig, raw.get("retrieval")),
        generation=_merge_dataclass(GenerationConfig, generation),
    )
