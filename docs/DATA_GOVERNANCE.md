# Data Governance — CAND-VB2 Verified Knowledge Base

Verified baseline: **2026-09-08 (Asia/Ho_Chi_Minh)**.

The objective is not to collect the largest corpus. The objective is to maintain the smallest corpus that can answer the target questions with **traceable, current, authoritative evidence**.

## 1. Evidence hierarchy

### A0 — authoritative core

Preferred whenever available:

1. Cơ sở dữ liệu văn bản Bộ Công an.
2. Cổng Thông tin điện tử Bộ Công an / official legal text hosted by Bộ Công an.
3. Cổng văn bản Chính phủ / official Bộ GDĐT legal publication.
4. Central Bộ Công an 2026 admissions/exam notices.

### A1 — official implementing institutions

Official websites of CAND academies/schools are used for school-specific quotas, local submission procedures, training duration and other institution-specific implementation details.

### Rejected as truth sources

News aggregators, commercial exam-prep centers, Facebook/TikTok posts, forums, SEO articles, anonymous documents and unsourced reposts are not admissible as answer evidence. They may be useful only for discovering a claim that must then be verified against A0/A1 material.

## 2. Temporal classes

Every source belongs to one temporal layer:

- **IN_FORCE** — legal/normative basis verified as effective or explicitly cited as current by authoritative 2026 guidance.
- **ANNUAL_2026** — quota, deadline, exam configuration and operational rules belonging to the 2026 intake only.
- **CURRENT_STATUS** — a dated operational snapshot; it becomes stale quickly.
- **WATCH_ONLY_DRAFT** — official draft/consultation material. It is a signal that rules may change, but it is **never indexed as answer evidence** before it is legally issued/effective.

This prevents the common RAG failure of treating a 2026 deadline or quota as a permanent rule.

## 3. Conflict resolution

When two official sources disagree:

1. Effective legal record / central Bộ Công an source outranks school prose on the same legal rule.
2. For school-specific implementation, that school's newest official notice is preferred unless it conflicts with a superior authority.
3. More specific current-year evidence outranks generic older guidance when both are legally compatible.
4. The conflict is logged in `data/known_source_issues.yaml`; it must not be silently hidden.
5. If the conflict cannot be resolved, the assistant must state that the official sources disagree and avoid a definitive conclusion.

## 4. The future-validity rule

No source is labelled "guaranteed for the future".

At the 2026-09-08 verification point:

- `99/2025/TT-BCA` is officially marked **Còn hiệu lực**, but a new Bộ Công an draft Circular on CAND admissions was under consultation from 13/08 to 23/08/2026. Therefore its **current validity is high-confidence while future stability is explicitly downgraded**.
- `131/2025/TT-BCA` is officially marked **Còn hiệu lực** and no newer health-replacement draft was found in the same verification pass. This is still not a promise that 2027 rules will be identical.
- annual 2026 quotas, dates and exam operations must expire from the "current" layer after the 2026 cycle and must never be copied into 2027 without a new source.

A commercial system should prefer a truthful warning over false permanence.

## 5. Snapshot policy

The repo commits curated Markdown snapshots containing paraphrased facts and source metadata, not scraped websites as unquestioned raw truth. Each snapshot should include:

```yaml
source_id: ...
authority: ...
official_url: ...
verified_at: 'YYYY-MM-DD'
status: ...
evidence_grade: A0 | A1
temporal_class: IN_FORCE | ANNUAL_2026 | CURRENT_STATUS
change_risk: ...
```

The original URL remains available for human audit.

## 6. Update policy

A full rebuild is needed only when vector-index inputs change: corpus content, chunking strategy, embedding model or embedding dimensions. Retrieval thresholds, reranker selection and generation model do not require re-embedding.

The persisted index carries a corpus fingerprint in `index_manifest.json`. If the fingerprint is unchanged, `scripts/build_index.py` skips Gemini re-embedding.

When new regulations appear:

1. verify the new source and effective date;
2. determine whether it supersedes/amends an existing source;
3. update `source_registry.yaml` and `known_source_issues.yaml`;
4. update the curated corpus;
5. run source validation and tests;
6. rebuild the persistent index once;
7. rerun retrieval/OOD/generation evaluation;
8. only then mark the dataset verification date as newer.

## 7. LightRAG ideas adopted selectively

The project was reviewed against HKUDS/LightRAG. We reimplemented only ideas that preserve the evidence-first contract for this corpus:

- heading-aware/paragraph-aware chunk boundaries;
- persistent/versioned index state;
- multi-view retrieval motivation implemented as dense + BM25 + RRF + source diversity + optional reranking.

We deliberately do **not** make an LLM-generated knowledge graph the production default. For a compact legal/admissions corpus, entity/relation extraction adds API calls and another hallucination surface. A graph path may be added only as an experimental ablation if it produces a statistically meaningful improvement on the held-out benchmark without reducing citation correctness or temporal precision.
