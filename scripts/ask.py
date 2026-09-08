from __future__ import annotations

import argparse

from vietrag.config import load_config
from vietrag.pipeline import VietRAGPipeline
from vietrag.providers import GeminiProvider, OpenRouterProvider
from vietrag.secrets import load_provider_env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--env", default="/content/providers.env")
    args = parser.parse_args()

    load_provider_env(args.env)
    cfg = load_config(args.config)
    rag = VietRAGPipeline.load(cfg, GeminiProvider(), OpenRouterProvider())
    ans = rag.ask(args.question)
    print(ans.text)
    print(rag.format_sources(ans))


if __name__ == "__main__":
    main()
