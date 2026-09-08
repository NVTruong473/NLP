from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Sequence

import requests
from google import genai
from google.genai import types

from .secrets import KeyPool, gemini_keys, openrouter_keys


class ProviderError(RuntimeError):
    pass


@dataclass
class ProviderModels:
    # default_factory is intentional: providers.env is loaded at runtime in Colab,
    # after this module may already have been imported.
    gemini_chat: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))
    gemini_embedding: str = field(
        default_factory=lambda: os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    )
    openrouter_chat: str = field(default_factory=lambda: os.getenv("OPENROUTER_CHAT_MODEL", "openrouter/free"))
    openrouter_rerank: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_RERANK_MODEL", "nvidia/llama-nemotron-rerank-vl-1b-v2:free"
        )
    )


class GeminiProvider:
    def __init__(self, keys: Sequence[str] | None = None, models: ProviderModels | None = None):
        self.pool = KeyPool(keys or gemini_keys())
        self.models = models or ProviderModels()

    def _attempt(self, fn):
        if not self.pool:
            raise ProviderError("No Gemini API key configured")
        errors: list[str] = []
        for key in self.pool.ordered():
            try:
                value = fn(key)
                self.pool.mark_success(key)
                return value
            except Exception as exc:
                self.pool.mark_failure(key)
                errors.append(type(exc).__name__)
                time.sleep(0.25)
        raise ProviderError(f"All Gemini keys failed ({', '.join(errors)})")

    def embed_documents(
        self,
        texts: Sequence[str],
        batch_size: int = 64,
        dimensions: int = 768,
    ) -> list[list[float]]:
        all_vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = list(texts[start : start + batch_size])

            def run(key: str):
                client = genai.Client(api_key=key)
                result = client.models.embed_content(
                    model=self.models.gemini_embedding,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=dimensions,
                    ),
                )
                return [list(e.values) for e in result.embeddings]

            all_vectors.extend(self._attempt(run))
        return all_vectors

    def embed_query(self, text: str, dimensions: int = 768) -> list[float]:
        def run(key: str):
            client = genai.Client(api_key=key)
            result = client.models.embed_content(
                model=self.models.gemini_embedding,
                contents=[text],
                config=types.EmbedContentConfig(
                    task_type="QUESTION_ANSWERING",
                    output_dimensionality=dimensions,
                ),
            )
            return list(result.embeddings[0].values)

        return self._attempt(run)

    def generate(self, prompt: str, temperature: float | None = None) -> str:
        def run(key: str):
            client = genai.Client(api_key=key)
            config = (
                types.GenerateContentConfig()
                if temperature is None
                else types.GenerateContentConfig(temperature=temperature)
            )
            response = client.models.generate_content(
                model=self.models.gemini_chat,
                contents=prompt,
                config=config,
            )
            if not getattr(response, "text", None):
                raise ProviderError("Gemini returned an empty response")
            return response.text.strip()

        return self._attempt(run)


class OpenRouterProvider:
    base_url = "https://openrouter.ai/api/v1"

    def __init__(self, keys: Sequence[str] | None = None, models: ProviderModels | None = None):
        self.pool = KeyPool(keys or openrouter_keys())
        self.models = models or ProviderModels()

    def _headers(self, key: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/NVTruong473/NLP",
            "X-OpenRouter-Title": "VietRAG",
        }

    def _post(self, endpoint: str, payload: dict, timeout: int = 90) -> dict:
        if not self.pool:
            raise ProviderError("No OpenRouter API key configured")
        errors: list[str] = []
        for key in self.pool.ordered():
            try:
                r = requests.post(
                    f"{self.base_url}/{endpoint.lstrip('/')}",
                    headers=self._headers(key),
                    json=payload,
                    timeout=timeout,
                )
                if r.status_code >= 400:
                    raise ProviderError(f"HTTP {r.status_code}")
                self.pool.mark_success(key)
                return r.json()
            except Exception as exc:
                self.pool.mark_failure(key)
                errors.append(str(exc)[:80])
                time.sleep(0.25)
        raise ProviderError(f"All OpenRouter keys failed ({'; '.join(errors)})")

    def generate(self, prompt: str, temperature: float | None = None) -> str:
        payload = {
            "model": self.models.openrouter_chat,
            "messages": [{"role": "user", "content": prompt}],
        }
        if temperature is not None:
            payload["temperature"] = temperature
        data = self._post("chat/completions", payload)
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise ProviderError(f"Unexpected OpenRouter response: {json.dumps(data)[:300]}") from exc

    def rerank(self, query: str, documents: Sequence[str], top_n: int) -> list[dict]:
        data = self._post(
            "rerank",
            {
                "model": self.models.openrouter_rerank,
                "query": query,
                "documents": list(documents),
                "top_n": top_n,
            },
        )
        return list(data.get("results", []))
