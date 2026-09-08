from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
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
    # A2 local police implementation sources
    "congan.camau.gov.vn",
    "congan.vinhlong.gov.vn",
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
ANSWER_GRADES = {"A0", "A1", "A2"}
LOCAL_SOURCE_TYPE = "official_local_police_implementation"


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def markdown_metadata(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.match(r"^---\s*\n(.*?)\n---", text, flags=re.S)
    if not match:
        return {}
    meta = yaml.safe_load(match.group(1)) or {}
    return meta if isinstance(meta, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CAND-VB2 source provenance.")
    parser.add_argument("--registry", default="data/source_registry.yaml")
    parser.add_argument("--local-registry", default="data/local_implementation_sources.yaml")
    parser.add_argument("--corpus", default="data/corpus")
    parser.add_argument("--live", action="store_true", help="Also perform best-effort HTTP reachability checks.")
    args = parser.parse_args()

    registry = load_yaml(Path(args.registry))
    local_registry = load_yaml(Path(args.local_registry)) if Path(args.local_registry).exists() else {}

    primary_sources = list(registry.get("sources") or [])
    local_sources = list(local_registry.get("sources") or [])
    answer_sources = primary_sources + local_sources
    watch_sources = list(registry.get("watch_only_sources") or [])
    all_sources = answer_sources + watch_sources

    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    grade_counts: Counter[str] = Counter()

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
        grade_counts[grade] += 1

        if item in answer_sources:
            if temporal not in ANSWER_CLASSES:
                errors.append(f"{sid}: answer source has invalid temporal class {temporal}")
            if grade not in ANSWER_GRADES:
                errors.append(f"{sid}: answer source must be A0/A1/A2, got {grade}")
            if grade == "A2" and item.get("source_type") != LOCAL_SOURCE_TYPE:
                errors.append(f"{sid}: A2 is restricted to {LOCAL_SOURCE_TYPE}")
            if item in local_sources and grade != "A2":
                errors.append(f"{sid}: local implementation registry must use A2")
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
                    headers={"User-Agent": "CAND-VB2-RAG-source-audit/1.1"},
                )
                if response.status_code >= 400:
                    warnings.append(f"{sid}: live HTTP {response.status_code}")
            except requests.RequestException as exc:
                warnings.append(f"{sid}: live check failed ({type(exc).__name__})")

    watch_ids = {str(x.get("id")) for x in watch_sources if x.get("id")}
    registered_answer_ids = {str(x["id"]) for x in answer_sources if x.get("id")}
    source_by_id = {str(x["id"]): x for x in answer_sources if x.get("id")}
    corpus_ids: set[str] = set()

    for path in sorted(Path(args.corpus).rglob("*.md")):
        try:
            meta = markdown_metadata(path)
        except yaml.YAMLError as exc:
            errors.append(f"{path}: invalid YAML frontmatter ({exc.__class__.__name__})")
            continue

        sid = str(meta.get("source_id")) if meta.get("source_id") else None
        if not sid:
            warnings.append(f"{path}: no source_id frontmatter")
            continue

        corpus_ids.add(sid)
        if sid in watch_ids:
            errors.append(f"{path}: WATCH_ONLY source {sid} must not be indexed in data/corpus")
        if sid not in registered_answer_ids:
            errors.append(f"{path}: source_id {sid} is not registered as answer evidence")
            continue

        registry_item = source_by_id[sid]
        expected_grade = str(registry_item.get("evidence_grade"))
        if meta.get("evidence_grade") and str(meta["evidence_grade"]) != expected_grade:
            errors.append(
                f"{path}: evidence_grade {meta['evidence_grade']} disagrees with registry {expected_grade}"
            )
        if expected_grade == "A2":
            # A2 may be indexed, but the prompt must see that it is local-only.
            if str(meta.get("change_risk", "")) != "locality_specific_annual":
                errors.append(f"{path}: A2 local snapshot must declare change_risk=locality_specific_annual")

    for warning in warnings:
        print("WARNING:", warning)
    for error in errors:
        print("ERROR:", error)

    grades = ", ".join(f"{k}={v}" for k, v in sorted(grade_counts.items()))
    print(
        f"Validated {len(answer_sources)} answer sources ({grades}), {len(watch_sources)} watch-only sources, "
        f"{len(corpus_ids)} corpus source IDs."
    )
    if errors:
        return 1
    print("Source governance validation: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
