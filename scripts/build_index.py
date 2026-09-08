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
    parser = argparse.ArgumentParser(
        description="Build the verified CAND-VB2 RAG index. Curated local corpus is the default for reproducibility."
    )
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument(
        "--sources",
        default="",
        help="Optional YAML of live URLs. Leave empty to use only verified snapshots committed in data/corpus.",
    )
    parser.add_argument("--input-dir", default="data/corpus")
    parser.add_argument("--env", default="/content/providers.env")
    args = parser.parse_args()

    load_provider_env(args.env)
    print("Loaded provider credentials (values hidden):", key_summary())
    cfg = load_config(args.config)
    segments = []

    if args.sources and Path(args.sources).is_file():
        source_cfg = yaml.safe_load(Path(args.sources).read_text(encoding="utf-8")) or {}
        for item in source_cfg.get("sources", []):
            url = item.get("url")
            if not url:
                continue
            print("Fetching live official source:", url)
            loaded = load_url(url)
            for segment in loaded:
                if item.get("id"):
                    segment.source = item["id"]
                if item.get("title"):
                    segment.title = item["title"]
                segment.authority = item.get("authority") or segment.authority
                segment.verified_at = item.get("verified_at") or segment.verified_at
                segment.status = item.get("status") or segment.status
                segment.scope = item.get("scope") or segment.scope
            segments.extend(loaded)

    if args.input_dir:
        root = Path(args.input_dir)
        if not root.exists():
            raise SystemExit(f"Input directory does not exist: {root}")
        for path in sorted(root.rglob("*")):
            if path.is_file():
                try:
                    loaded = load_path(path)
                    segments.extend(loaded)
                    print("Loaded verified snapshot:", path)
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
        raise SystemExit("No chunks were created. Check data/corpus or the supplied official sources.")

    sources = sorted({chunk.source for chunk in chunks})
    print(f"Corpus: {len(segments)} segments -> {len(chunks)} chunks from {len(sources)} source IDs")
    print("Source IDs:", ", ".join(sources))
    print(f"Embedding {len(chunks)} chunks with Gemini...")
    index = HybridIndex.build(chunks, GeminiProvider())
    index.save(cfg.index_dir)
    print(f"Index saved to {cfg.index_dir}")


if __name__ == "__main__":
    main()
