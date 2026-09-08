from __future__ import annotations

import os

import gradio as gr

from vietrag.config import load_config
from vietrag.pipeline import VietRAGPipeline
from vietrag.providers import GeminiProvider, OpenRouterProvider
from vietrag.secrets import load_provider_env


ENV_PATH = os.getenv("VIETRAG_ENV", "/content/providers.env")
CONFIG_PATH = os.getenv("VIETRAG_CONFIG", "configs/default.yaml")

load_provider_env(ENV_PATH)
config = load_config(CONFIG_PATH)
rag = VietRAGPipeline.load(config, GeminiProvider(), OpenRouterProvider())


def answer(message: str, history):
    result = rag.ask(message)
    return result.text + rag.format_sources(result)


demo = gr.ChatInterface(
    fn=answer,
    title="VietRAG — Evidence-First Vietnamese RAG",
    description=(
        "Hybrid retrieval (Gemini dense embeddings + BM25), optional OpenRouter reranking, "
        "domain refusal, and inline source citations."
    ),
    examples=[
        "TDTU có những phương thức tuyển sinh đại học nào trong năm 2026?",
        "Quy chế đào tạo áp dụng cho khóa tuyển sinh 2021 trở về sau quy định phạm vi nào?",
        "Hãy kể cho tôi công thức làm bánh tiramisu.",
    ],
)

if __name__ == "__main__":
    demo.launch(share=True)
