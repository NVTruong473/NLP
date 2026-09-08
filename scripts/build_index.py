from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from vietrag.chunking import chunk_segments
from vietrag.config import load_config
from vietrag.ingest import load_path, load_url
from vietrag.providers import GeminiProvider
from vietrag.retrieval import HybridIndex
from vietrag.secrets import key_summary, load_provider_env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--sources", default="data/demo_sources.yaml")
    parser.add_argument("--input-dir", default=None)
    parser.add_argument("--env", default="/content/providers.env")
    args = parser.parse_args()

    load_provider_env(args.env)
    print("Loaded provider credentials:", key_summary())
    cfg = load_config(args.config)
    segments = []

    if args.sources and Path(args.sources).is_file():
        source_cfg = yaml.safe_load(Path(args.sources).read_text(encoding="utf-8")) or {}
        for item in source_cfg.get("sources", []):
            url = item.get("url")
            if not url:
                continue
            print("Fetching:", url)
            loaded = load_url(url)
            # Preserve a stable, human-controlled source id when supplied.
            for segment in loaded:
                if item.get("id"):
                    segment.source = item["id"]
                if item.get("title"):
                    segment.title = item["title"]
            segments.extend(loaded)

    if args.input_dir:
        for path in sorted(Path(args.input_dir).rglob("*")):
            if path.is_file():
                try:
                    segments.extend(load_path(path))
                    print("Loaded:", path)
                except ValueError:
                    pass

    c = cfg.chunking
    chunks = chunk_segments(
        segments,
        chunk_words=c.chunk_words,
        overlap_words=c.overlap_words,
        min_chunk_words=c.min_chunk_words,
    )
    if not chunks:
        raise SystemExit("No chunks were created. Check your source URLs/files.")

    print(f"Embedding {len(chunks)} chunks with Gemini...")
    index = HybridIndex.build(chunks, GeminiProvider())
    index.save(cfg.index_dir)
    print(f"Index saved to {cfg.index_dir}")


if __name__ == "__main__":
    main()
