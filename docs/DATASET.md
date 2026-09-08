# Dataset Card — CAND-VB2-2026 Verified Knowledge Base

## Purpose

A compact, high-confidence corpus for a specialized RAG assistant about **VB2CA tuyển mới**: tuyển mới đào tạo trình độ đại học chính quy CAND đối với công dân đã có bằng tốt nghiệp đại học trở lên, with emphasis on applicants whose first degree is Computer Science / Information Technology.

**Verification snapshot:** 2026-09-08 (Vietnam time).

## Source policy

Only primary official sources are admissible as answer evidence:

### A0

1. Ministry of Public Security official portal (`bocongan.gov.vn`).
2. Ministry of Public Security legal-document database (`vanban.bocongan.gov.vn`).
3. Official Government/MOET legal publication (`vanban.chinhphu.vn`, official MOET domains where used).
4. Central Ministry 2026 admissions/exam/status notices.

### A1

Official CAND academy/school websites for institution-specific implementation details.

The truth set does **not** use newspapers, commercial coaching centers, forums, social-media posts, SEO pages or unsourced reposts as authoritative evidence.

## Reproducible snapshots

Government websites can change layout, rate-limit, move attachments or update content. Re-scraping on every notebook run would make evaluation non-reproducible.

Therefore:

- `data/corpus/*.md` contains concise, human-reviewed factual snapshots with YAML provenance;
- `data/source_registry.yaml` contains canonical source metadata and temporal class;
- `data/known_source_issues.yaml` records discovered source conflicts/typos;
- `data/official_sources.yaml` is optional for live-refresh experiments;
- the default Colab build indexes the committed corpus and persists the index to Google Drive.

Snapshots are paraphrased factual summaries, not mirrors of entire official webpages.

## Temporal model

The dataset does not treat all “official” facts as equally durable.

- **IN_FORCE** — legal/normative basis verified as effective or explicitly cited as current by authoritative 2026 guidance.
- **ANNUAL_2026** — quota, deadline, exam configuration and operational facts only for the 2026 cycle.
- **CURRENT_STATUS** — dated operational snapshot, rapidly stale.
- **WATCH_ONLY_DRAFT** — official draft/change signal; never indexed as current answer evidence.

### Important August 2026 change signal

On 13/08/2026, Bộ Công an opened consultation on a new draft Circular titled **“Thông tư quy định về tuyển sinh trong Công an nhân dân”**, with consultation ending 23/08/2026.

At 08/09/2026, `99/2025/TT-BCA` is still officially marked **Còn hiệu lực**, so current 2026 answers continue to use the existing legal framework and 2026 guidance. However, the new draft is direct evidence that **future stability is uncertain**. The system must not claim that 2026 admissions rules will remain unchanged for 2027.

By contrast, `131/2025/TT-BCA` is also marked **Còn hiệu lực** and the verification pass did not find a newer health-replacement draft. This lowers the observed change signal but does not guarantee future permanence.

## Deadline-sensitive rule

At 2026-09-08:

- the ordinary 2026 initial registration/screening window described by official school sources has passed;
- the August file-submission milestone has passed;
- the computer-based VB2CA assessment is still being prepared for 19–20/09/2026;
- no supplementary/late round is asserted without a newer official notice.

## Scope

Included:

- eligibility for an existing university-degree holder;
- IT/Computer Science-specific routes/exceptions;
- direct-admission vs exam method;
- preliminary screening and public document requirements;
- 2026 schedules;
- CA1–CA4 and computer-based exam structure;
- school/major/region rules;
- published health thresholds and legal basis;
- current legal status and future-change warnings;
- domain disambiguation between VB2CA tuyển mới and similarly named programs.

Excluded from authoritative answer evidence:

- second-degree programs for existing CAND officers;
- ordinary THPT-entry CAND admission facts unless needed only to explain domain confusion;
- predictions, rumors and coaching-center advice;
- private/internal political screening details not publicly published;
- medical diagnosis or definitive health adjudication;
- draft rules as if they were effective law;
- future 2027 facts until a new verified dataset version is created.

## Versioning and persistence

`build_index.py` fingerprints corpus content, chunking configuration, embedding model and embedding dimensions. The persisted Google Drive index includes `index_manifest.json`.

If the fingerprint is unchanged, the build is skipped and Gemini embeddings are not called again. Retrieval settings, reranker choice and generation model can change without rebuilding the vector index.

## Known limitations

A high-confidence curated dataset is still not a substitute for the competent police authority. Final political-standard, health, preliminary-screening and enrollment decisions belong to the official process. Public HTML pages may omit appendices or internal implementation detail.

For any later intake, re-verify the source registry and legal watchlist rather than assuming the 2026 snapshot remains current.

See [Data Governance](DATA_GOVERNANCE.md) for authority ordering and conflict policy.
