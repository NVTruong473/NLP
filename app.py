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
    title="CAND-VB2 RAG — Trợ lý tuyển sinh Văn bằng 2 Công an 2026",
    description=(
        "Dataset chỉ dùng nguồn chính thức Bộ Công an/trường CAND, xác minh đến 08/09/2026. "
        "Hỏi về điều kiện bằng CNTT, sơ tuyển, hồ sơ, kỳ thi, trường/ngành, sức khỏe và lịch 2026. "
        "Mọi câu trả lời phải có bằng chứng [S#]."
    ),
    examples=[
        "Tôi có bằng đại học CNTT loại Khá thì năm 2026 có thể dự tuyển VB2 Công an theo hướng nào?",
        "Nếu tôi chưa đăng ký sơ tuyển trước ngày 15/6/2026 thì bây giờ 8/9/2026 còn đăng ký được không?",
        "Kỳ thi VB2CA 2026 thi ngày nào, trên máy tính ra sao và CA1 gồm những gì?",
        "Bằng CNTT có thể đăng ký ngành An toàn thông tin của Học viện An ninh nhân dân không?",
        "Nam học CNTT cao 1m62 có phù hợp ngưỡng sức khỏe được công bố không?",
        "Văn bằng 2 dành cho cán bộ CAND có phải cùng chương trình VB2CA tuyển mới không?",
        "Cho tôi công thức làm bánh tiramisu.",
    ],
)

if __name__ == "__main__":
    demo.launch(share=True)
