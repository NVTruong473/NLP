from __future__ import annotations

import re
from dataclasses import dataclass

from .config import AppConfig
from .guardrails import INSUFFICIENT, build_grounded_prompt, should_refuse
from .providers import GeminiProvider, OpenRouterProvider, ProviderError
from .retrieval import HybridIndex, RetrievedChunk


@dataclass
class Answer:
    text: str
    sources: list[RetrievedChunk]
    provider: str
    top_dense_score: float
    refused: bool = False


class VietRAGPipeline:
    def __init__(
        self,
        index: HybridIndex,
        config: AppConfig,
        gemini: GeminiProvider,
        openrouter: OpenRouterProvider | None = None,
    ):
        self.index = index
        self.config = config
        self.gemini = gemini
        self.openrouter = openrouter

    @classmethod
    def load(
        cls,
        config: AppConfig,
        gemini: GeminiProvider,
        openrouter: OpenRouterProvider | None = None,
    ):
        index = HybridIndex.load(config.index_dir, embedder=gemini)
        return cls(index=index, config=config, gemini=gemini, openrouter=openrouter)

    @staticmethod
    def _sanitize_citations(text: str, source_count: int) -> str:
        """Remove impossible [S#] references while preserving valid citations."""
        def repl(match: re.Match) -> str:
            number = int(match.group(1))
            return match.group(0) if 1 <= number <= source_count else ""

        return re.sub(r"\[S(\d+)\]", repl, text)

    def ask(self, question: str) -> Answer:
        if not question.strip():
            return Answer(INSUFFICIENT, [], provider="none", top_dense_score=-1.0, refused=True)

        r = self.config.retrieval
        results, top_dense = self.index.search(
            question,
            dense_top_k=r.dense_top_k,
            bm25_top_k=r.bm25_top_k,
            fusion_top_k=r.fusion_top_k,
            rrf_k=r.rrf_k,
            dense_weight=r.dense_weight,
            bm25_weight=r.bm25_weight,
            max_chunks_per_source=r.max_chunks_per_source,
            reranker=self.openrouter,
            rerank_top_k=r.rerank_top_k,
        )
        if should_refuse(results, top_dense, r.ood_dense_threshold):
            return Answer(
                INSUFFICIENT,
                results,
                provider="none",
                top_dense_score=top_dense,
                refused=True,
            )

        prompt = build_grounded_prompt(
            question,
            results,
            self.config.generation.max_context_chars,
        )
        errors: list[str] = []
        for provider in self.config.generation.provider_order:
            try:
                if provider == "gemini":
                    text = self.gemini.generate(
                        prompt,
                        temperature=self.config.generation.temperature,
                    )
                elif provider == "openrouter" and self.openrouter is not None:
                    text = self.openrouter.generate(
                        prompt,
                        temperature=self.config.generation.temperature,
                    )
                else:
                    continue

                text = self._sanitize_citations(text.strip(), len(results))
                refused = text == INSUFFICIENT
                return Answer(
                    text=text,
                    sources=results,
                    provider=provider,
                    top_dense_score=top_dense,
                    refused=refused,
                )
            except ProviderError as exc:
                errors.append(f"{provider}: {exc}")
        raise ProviderError("No generation provider succeeded: " + " | ".join(errors))

    @staticmethod
    def format_sources(answer: Answer) -> str:
        if not answer.sources:
            return ""
        lines = ["\n\n### Bằng chứng chính thức đã truy xuất"]
        for i, item in enumerate(answer.sources, start=1):
            label = item.chunk.title or item.chunk.source
            meta: list[str] = []
            if item.chunk.section:
                meta.append(f"mục: {item.chunk.section}")
            if item.chunk.authority:
                meta.append(item.chunk.authority)
            if item.chunk.verified_at:
                meta.append(f"xác minh {item.chunk.verified_at}")
            if item.chunk.status:
                meta.append(f"{item.chunk.status}")
            if item.chunk.page is not None:
                meta.append(f"trang {item.chunk.page}")
            score_bits = []
            if item.dense_score is not None:
                score_bits.append(f"dense={item.dense_score:.3f}")
            if item.rerank_score is not None:
                score_bits.append(f"rerank={item.rerank_score:.3f}")
            if score_bits:
                meta.append(", ".join(score_bits))

            line = f"- [S{i}] **{label}**"
            if meta:
                line += f" — {'; '.join(meta)}"
            if item.chunk.url:
                line += f"\n  {item.chunk.url}"
            lines.append(line)
        return "\n".join(lines)
