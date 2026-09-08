# Data — CAND-VB2-2026

The default dataset is a **curated, verified knowledge corpus** about 2026 VB2CA tuyển mới: recruitment into regular CAND university training for citizens who already hold a university degree, with special attention to first-degree IT/Computer Science candidates.

## What is committed

- `corpus/*.md` — concise factual snapshots with YAML provenance (`source_id`, authority, official URL, publication/verification date, current status and scope).
- `source_registry.yaml` — canonical registry of every official source accepted into the truth set.
- `official_sources.yaml` — optional live URLs for refreshing/experimental crawling.

The Colab default indexes `data/corpus/`; it does **not** need to crawl websites at runtime. This makes the experiment reproducible and prevents a temporary government-site outage or HTML change from breaking the demo.

## Evidence policy

Only official primary sources are authoritative:

- Ministry of Public Security portal;
- Ministry of Public Security legal-document database;
- official CAND academy/school websites.

News sites, forums, Facebook groups, TikTok, coaching centers and other unofficial pages are excluded from the curated truth set.

**Verified as of: 2026-09-08 (Vietnam time).** See `docs/DATASET.md` for scope, temporal-validity rules and limitations.

## Optional custom ingestion

The generic engine can still ingest text-based PDF, DOCX, TXT/Markdown, HTML or explicit HTTP(S) URLs. Put experimental files under `data/uploads/`; the path is Git-ignored. Custom files are not part of the verified VB2CA dataset unless separately reviewed and registered.
