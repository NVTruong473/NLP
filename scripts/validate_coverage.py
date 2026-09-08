from __future__ import annotations

import sys
from pathlib import Path

import yaml


VALID_STATUSES = {"verified", "partial_public"}


def load_yaml(path: str) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def main() -> int:
    coverage = load_yaml("data/coverage_matrix.yaml")
    registry = load_yaml("data/source_registry.yaml")
    local = load_yaml("data/local_implementation_sources.yaml")

    source_ids = {
        str(x["id"])
        for x in list(registry.get("sources") or []) + list(local.get("sources") or [])
        if x.get("id")
    }
    allowed_partial = set(coverage.get("allowed_partial_topics") or [])
    topics = coverage.get("topics") or {}

    errors: list[str] = []
    verified_critical = total_critical = 0
    verified_all = total_all = 0

    if not topics:
        errors.append("coverage_matrix has no topics")

    for name, item in topics.items():
        if not isinstance(item, dict):
            errors.append(f"{name}: expected mapping")
            continue
        status = str(item.get("status", ""))
        critical = bool(item.get("critical", False))
        sources = [str(x) for x in item.get("sources", [])]

        total_all += 1
        total_critical += int(critical)

        if status not in VALID_STATUSES:
            errors.append(f"{name}: invalid status {status!r}")
            continue
        if status == "partial_public" and name not in allowed_partial:
            errors.append(f"{name}: partial_public is not allow-listed")
        if critical and status != "verified":
            errors.append(f"{name}: critical topic must be verified, got {status}")
        if not sources:
            errors.append(f"{name}: no evidence sources")

        unknown = sorted(set(sources) - source_ids)
        if unknown:
            errors.append(f"{name}: unknown evidence sources {unknown}")

        if status == "verified":
            verified_all += 1
            verified_critical += int(critical)

    target = float(coverage.get("confidence_target", 0.95))
    critical_ratio = verified_critical / total_critical if total_critical else 0.0
    all_ratio = verified_all / total_all if total_all else 0.0

    # Commercial-readiness gate: every critical public topic must be verified.
    if critical_ratio < 1.0:
        errors.append(f"critical coverage {critical_ratio:.1%} < 100%")
    # Overall public-data coverage target may include transparent partial-public gaps.
    if (verified_all + len(allowed_partial.intersection(topics))) / total_all < target:
        errors.append(f"known/verified coverage below target {target:.0%}")

    print(f"Critical verified coverage: {verified_critical}/{total_critical} = {critical_ratio:.1%}")
    print(f"Fully verified topic coverage: {verified_all}/{total_all} = {all_ratio:.1%}")
    print(f"Transparent public gaps: {sorted(allowed_partial.intersection(topics))}")

    for error in errors:
        print("ERROR:", error)
    if errors:
        return 1
    print("Coverage validation: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
