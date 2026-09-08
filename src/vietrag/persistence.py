from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MANIFEST_NAME = "index_manifest.json"


def _files_under(paths: Iterable[str | Path]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(p for p in path.rglob("*") if p.is_file())
    return sorted(files, key=lambda p: p.as_posix())


def corpus_fingerprint(
    paths: Iterable[str | Path],
    *,
    chunking: dict[str, Any],
    embedding_model: str,
    embedding_dimensions: int,
) -> str:
    """Fingerprint only inputs that materially change the vector index.

    Retrieval thresholds, reranker choice and generation model are deliberately
    excluded: they can change without re-embedding the corpus.
    """
    digest = hashlib.sha256()
    for path in _files_under(paths):
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")

    build_params = {
        "chunking": chunking,
        "embedding_model": embedding_model,
        "embedding_dimensions": embedding_dimensions,
    }
    digest.update(json.dumps(build_params, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return digest.hexdigest()


def write_manifest(
    index_dir: str | Path,
    *,
    fingerprint: str,
    source_ids: list[str],
    segment_count: int,
    chunk_count: int,
    chunking: dict[str, Any],
    embedding_model: str,
    embedding_dimensions: int,
) -> Path:
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "fingerprint": fingerprint,
        "embedding_model": embedding_model,
        "embedding_dimensions": embedding_dimensions,
        "chunking": chunking,
        "segment_count": segment_count,
        "chunk_count": chunk_count,
        "source_ids": source_ids,
    }
    path = index_dir / MANIFEST_NAME
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_manifest(index_dir: str | Path) -> dict[str, Any] | None:
    path = Path(index_dir) / MANIFEST_NAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def index_ready(index_dir: str | Path) -> bool:
    index_dir = Path(index_dir)
    return all(
        (index_dir / name).is_file()
        for name in ("faiss.index", "chunks.jsonl", MANIFEST_NAME)
    )
