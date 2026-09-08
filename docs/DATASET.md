# Dataset Card — CAND-VB2-2026 Verified Knowledge Base

## Purpose

A small, high-confidence knowledge corpus for a specialized RAG assistant about **VB2CA tuyển mới**: tuyển mới đào tạo trình độ đại học chính quy Công an nhân dân đối với công dân đã có bằng tốt nghiệp trình độ đại học trở lên, with emphasis on candidates whose first degree is Computer Science / Information Technology.

**Verification snapshot:** 2026-09-08 (Vietnam time).

## Source policy

Only Grade-A primary sources are accepted into the curated corpus:

1. Ministry of Public Security official portal (`bocongan.gov.vn`).
2. Ministry of Public Security official legal-document database (`vanban.bocongan.gov.vn`).
3. Official CAND academy/school websites.

The curated truth set does **not** use news aggregators, newspapers, training centers, blogs, forums, Reddit, Facebook groups, TikTok, or SEO pages as authoritative evidence.

`data/source_registry.yaml` records every canonical source, authority, URL, evidence grade, status, and verification date.

## Why snapshots are committed instead of scraping on every run

Government websites may change layout, rate-limit requests, remove attachments, or be temporarily unavailable. A reproducible RAG experiment should not silently change its corpus every time a notebook is executed.

Therefore:

- `data/corpus/*.md` contains concise, human-reviewed factual snapshots with YAML provenance frontmatter.
- `data/official_sources.yaml` contains optional live URLs for re-checking or experimental live ingestion.
- Google Colab builds the default FAISS/BM25 index from the committed snapshots, so a clone can run immediately.

The snapshots are paraphrased factual summaries, not mirrors of entire official webpages.

## Temporal validity rules

- Annual admissions facts must come from 2026 sources for the 2026 intake.
- Legal documents are accepted as current only when the official legal database marks them in force at the verification date.
- If an older rule conflicts with a 2026 notice or an amending legal document, the newer/current authority wins.
- Deadline-sensitive answers must consider the verification date. At 2026-09-08, the ordinary 2026 initial registration window (15/03–15/06) and 20/08 file-submission milestone have already passed, while the 20/09 computer-based VB2CA exam is still upcoming in the verified official plan.
- The system must not invent a late-registration or supplementary round without a newer official notice.

## Scope boundary

Included:

- eligibility for holders of an existing bachelor degree;
- IT/Computer Science-specific pathways and exceptions;
- application/sơ tuyển procedure and documents;
- 2026 timeline;
- direct admission versus exam route;
- computer-based exam structure and CA1–CA4;
- school/major scope and regional rules;
- published health criteria and current legal basis;
- current 2026 status.

Excluded from the truth set:

- second-degree programs for **existing CAND officers**;
- ordinary police-university admission directly from high school;
- unverified rumors, predicted cutoffs, coaching-center advice;
- individual political-background adjudication or medical diagnosis;
- future 2027 rules unless the dataset is explicitly re-verified and versioned.

## Known limitations

This is a high-confidence curated corpus, not a complete copy of every internal Ministry instruction. Political-standard assessment and final health eligibility are performed by competent police authorities and cannot be inferred reliably by an LLM. Some appendices/attachments may contain more detail than public HTML pages.

Before using this system for a later admission cycle, create a new dataset version and re-verify every source rather than assuming 2026 rules remain unchanged.
