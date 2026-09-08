from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml


ALLOWED_OFFICIAL_HOSTS = {
    "bocongan.gov.vn",
    "www.bocongan.gov.vn",
    "vanban.bocongan.gov.vn",
    "hvannd.edu.vn",
    "www.hvannd.edu.vn",
    "hvcsnd.edu.vn",
    "www.hvcsnd.edu.vn",
    "dhannd.bocongan.gov.vn",
    "dhcsnd.edu.vn",
    "www.dhcsnd.edu.vn",
    "hvktcnan.bocongan.gov.vn",
    "hocvienpccc.bocongan.gov.vn",
    "vanban.chinhphu.vn",
    "tuyensinh.moet.gov.vn",
    "moet.gov.vn",
    "www.moet.gov.vn",
}

REQUIRED = {
    "id",
    "authority",
    "title",
    "url",
    "source_type",
    "temporal_class",
    "status",
    "evidence_grade",
    "verified_at",
}

ANSWER_CLASSES = {"IN_FORCE", "ANNUAL_2026", "CURRENT_STATUS"}
WATCH_CLASS = "WATCH_ONLY_DRAFT"


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def markdown_source_id(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.match(r"^---\s*\n(.*?)\n---", text, flags=re.S)
    if not match:
        return None
    meta = yaml.safe_load(match.group(1)) or {}
    return str(meta.get("source_id")) if isinstance(meta, dict) and meta.get("source_id") else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CAND-VB2 source provenance.")
    parser.add_argument("--registry", default="data/source_registry.yaml")
    parser.add_argument("--corpus", default="data/corpus")
    parser.add_argument("--live", action="store_true", help="Also perform best-effort HTTP reachability checks.")
    args = parser.parse_args()

    registry = load_yaml(Path(args.registry))
    answer_sources = list(registry.get("sources") or [])
    watch_sources = list(registry.get("watch_only_sources") or [])
    all_sources = answer_sources + watch_sources

    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()

    for item in all_sources:
        missing = sorted(REQUIRED - set(item))
        if missing:
            errors.append(f"{item.get('id', '<unknown>')}: missing {missing}")
            continue
        sid = str(item["id"])
        if sid in seen:
            errors.append(f"duplicate source id: {sid}")
        seen.add(sid)

        host = (urlparse(str(item["url"])).hostname or "").lower()
        if host not in ALLOWED_OFFICIAL_HOSTS:
            errors.append(f"{sid}: non-approved host {host!r}")

        grade = str(item["evidence_grade"])
        temporal = str(item["temporal_class"])
        if item in answer_sources:
            if temporal not in ANSWER_CLASSES:
                errors.append(f"{sid}: answer source has invalid temporal class {temporal}")
            if grade not in {"A0", "A1"}:
                errors.append(f"{sid}: answer source must be A0 or A1, got {grade}")
        else:
            if temporal != WATCH_CLASS:
                errors.append(f"{sid}: watch-only source must use {WATCH_CLASS}")
            if item.get("retrieval_policy") != "never_index_as_answer_evidence":
                errors.append(f"{sid}: watch-only source lacks safe retrieval_policy")

        if args.live:
            try:
                response = requests.get(
                    str(item["url"]),
                    timeout=20,
                    allow_redirects=True,
                    headers={"User-Agent": "CAND-VB2-RAG-source-audit/1.0"},
                )
                if response.status_code >= 400:
                    warnings.append(f"{sid}: live HTTP {response.status_code}")
            except requests.RequestException as exc:
                warnings.append(f"{sid}: live check failed ({type(exc).__name__})")

    watch_ids = {str(x.get("id")) for x in watch_sources if x.get("id")}
    corpus_ids: set[str] = set()
    for path in sorted(Path(args.corpus).rglob("*.md")):
        sid = markdown_source_id(path)
        if sid:
            corpus_ids.add(sid)
            if sid in watch_ids:
                errors.append(f"{path}: WATCH_ONLY source {sid} must not be indexed in data/corpus")
        else:
            warnings.append(f"{path}: no source_id frontmatter")

    registered_answer_ids = {str(x["id"]) for x in answer_sources if x.get("id")}
    unknown_corpus = sorted(corpus_ids - registered_answer_ids)
    if unknown_corpus:
        errors.append(f"corpus source_ids not registered as answer sources: {unknown_corpus}")

    for warning in warnings:
        print("WARNING:", warning)
    for error in errors:
        print("ERROR:", error)

    print(
        f"Validated {len(answer_sources)} answer sources, {len(watch_sources)} watch-only sources, "
        f"{len(corpus_ids)} corpus source IDs."
    )
    if errors:
        return 1
    print("Source governance validation: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
