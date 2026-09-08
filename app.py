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
    title="CAND-VB2 RAG — Trợ lý VB2 Công an có bằng chứng",
    description=(
        "Nguồn chính thức A0/A1, snapshot xác minh đến 08/09/2026. "
        "Hệ thống phân biệt quy định đang có hiệu lực, thông tin riêng kỳ 2026 và tín hiệu dự thảo tương lai. "
        "Mỗi câu trả lời phải bám bằng chứng [S#]; dự thảo không được dùng như luật hiện hành."
    ),
    examples=[
        "Tôi có bằng đại học CNTT loại Khá thì năm 2026 có thể dự tuyển VB2 Công an theo hướng nào?",
        "Ngành An toàn thông tin Học viện ANND có bao nhiêu chỉ tiêu VB2 năm 2026 và bằng 1 cần thuộc lĩnh vực nào?",
        "Nếu tôi chưa đăng ký sơ tuyển trước ngày 15/6/2026 thì bây giờ 8/9/2026 còn đăng ký được không?",
        "Kỳ thi VB2CA 2026 tổ chức 19-20/9 hay thi chính ngày 20/9?",
        "Nam tốt nghiệp CNTT cao 1m62 thì ngưỡng chiều cao công khai ở Học viện CSND nói gì?",
        "Thông tư 99/2025/TT-BCA đang còn hiệu lực, vậy có chắc năm 2027 giữ nguyên không?",
        "Văn bằng 2 dành cho cán bộ CAND có phải cùng chương trình VB2CA tuyển mới không?",
        "Cho tôi công thức làm bánh tiramisu.",
    ],
)

if __name__ == "__main__":
    demo.launch(share=True)
