# CAND‑VB2 RAG — Verified Police Second‑Degree Admissions Assistant

> Personal RAG project for **tuyển mới đào tạo đại học chính quy Công an nhân dân đối với công dân đã có bằng đại học trở lên (VB2CA tuyển mới)**, with special attention to applicants whose first degree is **CNTT / Computer Science / IT**.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Colab](https://img.shields.io/badge/Google%20Colab-Quick%20Resume-orange)](https://colab.research.google.com/github/NVTruong473/NLP/blob/main/notebooks/VietRAG_Colab.ipynb)
[![Dataset](https://img.shields.io/badge/Data-official%20sources%20only-success)](data/source_registry.yaml)
[![Verified](https://img.shields.io/badge/verified-2026--09--08-brightgreen)](data/source_registry.yaml)
[![CI](https://img.shields.io/github/actions/workflow/status/NVTruong473/NLP/tests.yml?label=provenance%20%2B%20tests)](.github/workflows/tests.yml)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## What this project does

This is not a generic chatbot and not a crawler that blindly indexes every page containing the phrase “văn bằng 2”. It is an **evidence-first, time-aware RAG system** designed to answer questions such as:

- I have an IT degree — which VB2CA routes are relevant in 2026?
- Is field code `748` accepted by a particular academy?
- What academic classification/GPA conditions apply?
- Where is preliminary screening performed and what documents are needed?
- Is normal registration still open on 08/09/2026?
- What are CA1–CA4 and how is the computer-based test organized?
- Which public height/BMI/vision thresholds are relevant to an IT graduate?
- Which legal rules are currently effective, and which facts are only annual 2026 rules?
- Can a 2026 rule safely be assumed for 2027? **Usually no — the system explains why.**

Every factual answer is expected to cite retrieved official evidence as `[S1]`, `[S2]`, … and expose the official URL, authority and verification date.

---

# ⚠️ Current legal-status warning — 08/09/2026

At the verification baseline **08 September 2026**:

- Bộ Công an reports **530** VB2CA tuyển mới seats system-wide for 2026.
- It reports **5,123 Method-2 applicants**.
- The computer-based VB2CA assessment is being organized for **19–20/09/2026**; the specific exam-structure notice identifies **20/09/2026** as the main test date.
- The ordinary initial registration window and August file-submission milestones have already passed. The assistant must not invent a late-registration round.
- `99/2025/TT-BCA` is officially marked **Còn hiệu lực** from 06/01/2026.
- `131/2025/TT-BCA`, amending the special CAND health rules, is officially marked **Còn hiệu lực** from 25/12/2025.

### A critical future-change signal

Bộ Công an opened official consultation from **13/08/2026 to 23/08/2026** on a new draft Circular titled **“Thông tư quy định về tuyển sinh trong Công an nhân dân”**.

That draft is **not law** and is never used as answer evidence. But its existence means the current admissions framework must **not** be described as likely unchanged for 2027. The project therefore tracks it separately as `WATCH_ONLY_DRAFT`.

This distinction is intentional:

```text
valid now ≠ guaranteed unchanged later
```

See [Data Governance](docs/DATA_GOVERNANCE.md) and [Known Source Issues](data/known_source_issues.yaml).

---

# Exact domain boundary

The project covers:

**VB2CA tuyển mới** — recruitment into full-time CAND undergraduate training for a Vietnamese citizen who already holds a university degree.

It deliberately separates this from:

1. second-degree/university programs for **existing CAND officers**;
2. ordinary CAND undergraduate recruitment from **THPT**;
3. civilian second-degree programs;
4. postgraduate CAND education.

Mixing those programs is one of the easiest ways for a RAG system to generate a confident but wrong answer.

---

# Architecture

```text
Verified official sources
        │
        ▼
Authority + effective-date + conflict audit
        │
        ▼
Curated Markdown snapshots + provenance
        │
        ▼
Heading-aware semantic sections
        │
        ├───────────────┐
        ▼               ▼
Gemini Embeddings      BM25
        │               │
        └──────┬────────┘
               ▼
      Reciprocal Rank Fusion
               │
               ▼
       source-diversity filter
               │
               ▼
 OpenRouter reranker (optional/free)
               │
               ▼
 retrieval-confidence / OOD gate
               │
       ┌───────┴────────┐
     refuse          answerable
                         │
                         ▼
              grounded generation
              Gemini → OpenRouter
                   fallback
                         │
                         ▼
       answer + [S#] + official URLs
```

**External AI APIs: Gemini + OpenRouter only.**

- Gemini: embeddings and primary generation.
- OpenRouter: generation fallback and optional reranking.
- FAISS, BM25, parsing, provenance validation, evaluation and Gradio run locally in Colab/runtime.

---

# Dataset design

The project favors **authoritative coverage**, not maximum scrape volume.

```text
data/
├── corpus/
│   ├── 00_current_status_2026-09-08.md
│   ├── 01_eligibility_for_it_graduates.md
│   ├── 02_registration_documents_timeline.md
│   ├── 03_exam_structure_2026.md
│   ├── 04_health_standards_current.md
│   ├── 05_legal_basis_in_force.md
│   ├── 05b_health_law_in_force.md
│   ├── 06_school_options_for_it.md
│   ├── 07_t07_technical_security_academy_2026.md
│   ├── 08_scope_and_disambiguation.md
│   ├── 09_hvannd_vb2_2026.md
│   ├── 10_hvcsnd_vb2_2026.md
│   ├── 11_dhannd_vb2_2026.md
│   ├── 12_dhcsnd_vb2_2026.md
│   ├── 13_pccc_vb2_2026.md
│   └── 14_moet_legal_basis_2026.md
├── source_registry.yaml
├── known_source_issues.yaml
└── official_sources.yaml
```

Each curated snapshot contains metadata such as:

```yaml
source_id: HVCSND-VB2-2026
authority: Học viện Cảnh sát nhân dân
official_url: https://...
verified_at: '2026-09-08'
status: current_for_2026_intake
evidence_grade: A1
temporal_class: ANNUAL_2026
change_risk: annual_expiry
```

That metadata survives chunking and is available to the grounded-generation prompt.

## Evidence grades

- **A0** — Bộ Công an legal database, central Bộ Công an portal, official Government/MOET legal publication.
- **A1** — official academy/school implementation notice.

Commercial coaching sites, news aggregators, forums, TikTok/Facebook posts and unsourced reposts are not admitted to the truth set.

## Temporal classes

- `IN_FORCE` — current normative/legal basis at the verification date.
- `ANNUAL_2026` — 2026-only quota, deadlines, exam setup and operational rules.
- `CURRENT_STATUS` — dated live status; becomes stale rapidly.
- `WATCH_ONLY_DRAFT` — official draft/change signal; **never indexed as current answer evidence**.

---

# Important official sources

The source registry includes, among others:

- Bộ Công an — central 2026 admissions information:  
  `https://www.bocongan.gov.vn/bai-viet/thong-tin-tuyen-sinh-cac-hoc-vien-truong-cong-an-nhan-dan-nam-2026-1773897621`
- Bộ Công an — VB2CA computer-test structure:  
  `https://bocongan.gov.vn/bai-viet/cong-bo-de-thi-minh-hoa-ky-thi-van-bang-2-cong-an-tren-may-tinh-1781667002`
- Bộ Công an — status review on 08/09/2026:  
  `https://www.bocongan.gov.vn/bai-viet/ra-soat-cong-tac-to-chuc-ky-thi-danh-gia-tren-may-tinh-va-ban-ve-de-an-dua-tieng-anh-tro-thanh-ngon-ngu-thu-hai-trong-truong-hoc-1788850887`
- CSDL văn bản Bộ Công an — `99/2025/TT-BCA`.
- CSDL văn bản Bộ Công an — `131/2025/TT-BCA`.
- Government legal portal — `06/2026/TT-BGDĐT` and `08/2021/TT-BGDĐT`.
- Official 2026 VB2 notices from Học viện ANND, Học viện CSND, Trường ĐH ANND, Trường ĐH CSND, Học viện Kỹ thuật & Công nghệ an ninh, and Trường ĐH PCCC.

The complete machine-readable list is [data/source_registry.yaml](data/source_registry.yaml).

---

# Source conflicts are not hidden

A trustworthy legal/admissions RAG should not silently choose whichever chunk happens to rank first.

Example already recorded in this dataset: one Học viện ANND 2026 page appears to contain a health-circular number typo. The official Bộ Công an legal database and multiple current official notices establish `131/2025/TT-BCA` as the amendment to `62/2023/TT-BCA`, so the project records and resolves the issue explicitly.

See [data/known_source_issues.yaml](data/known_source_issues.yaml).

---

# LightRAG: what was borrowed and what was rejected

This project reviewed **HKUDS/LightRAG** and its GraphRAG-style architecture.

Useful ideas were **reimplemented**, not copied blindly:

- heading/paragraph-aware document segmentation;
- persistent/versioned index state;
- multi-view retrieval motivation;
- reranking and citation-first retrieval diagnostics.

For this particular domain, the production default **does not use an LLM-generated knowledge graph**. The reason is practical: the corpus is compact, highly regulated and evidence-sensitive; generic entity/relation extraction adds LLM calls, latency and another hallucination surface.

The current retrieval path instead uses:

```text
Dense + BM25 + RRF + source diversity + reranker
```

A graph path should be added only as an **ablation experiment** if it measurably improves held-out retrieval/generation metrics without reducing citation correctness, temporal precision or robustness.

Reference: `https://github.com/HKUDS/LightRAG` and LightRAG paper `https://arxiv.org/abs/2410.05779`.

---

# Google Colab — two operating modes

Open:

[**CAND‑VB2 RAG Colab notebook**](https://colab.research.google.com/github/NVTruong473/NLP/blob/main/notebooks/VietRAG_Colab.ipynb)

## Mode A — FULL UPDATE / BUILD

Run this only:

- the first time;
- after verified dataset content changes;
- after changing chunking strategy;
- after changing the embedding model/dimensions.

The notebook saves the expensive knowledge artifacts to:

```text
/content/drive/MyDrive/CAND_VB2_RAG/index/
├── faiss.index
├── chunks.jsonl
└── index_manifest.json
```

The manifest contains a fingerprint of corpus + embedding inputs. `build_index.py` skips Gemini re-embedding when that fingerprint is unchanged.

## Mode B — QUICK RESUME & CHAT

**For normal later use, run only the final notebook cell.**

The final cell is self-contained. On a fresh Colab runtime it:

1. mounts Google Drive;
2. verifies the saved index exists;
3. clones/pulls the latest repo code;
4. installs runtime dependencies only if missing;
5. checks `/content/providers.env` and asks you to upload it if necessary;
6. points the app to the saved Drive index;
7. launches Gradio.

It intentionally **does not run `build_index.py`**, does not crawl official websites and does not call Gemini embeddings again.

If the saved index is missing, Quick Resume stops and tells you to perform one Full Build rather than silently consuming quota.

---

# `providers.env`

Create your private file from [providers.env.example](providers.env.example):

```dotenv
GEMINI_API_KEY_1=YOUR_KEY
# GEMINI_API_KEY_2=OPTIONAL
GEMINI_MODEL=gemini-3.8-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

OPENROUTER_API_KEY_1=YOUR_KEY
OPENROUTER_CHAT_MODEL=openrouter/free
OPENROUTER_RERANK_MODEL=nvidia/llama-nemotron-rerank-vl-1b-v2:free
```

Upload it in Colab to:

```text
/content/providers.env
```

Only Gemini and OpenRouter API credentials are used. The word `nvidia` above is an **OpenRouter model identifier**; there is no NVIDIA API integration.

Never commit real keys. A file committed to a public GitHub repository cannot be owner-only. See [SECURITY.md](SECURITY.md).

---

# Retrieval design

## 1. Heading-aware chunks

Curated Markdown is split on heading boundaries before word-window chunking. A section such as:

```text
Điều kiện > Độ tuổi
```

stays semantically separate from unrelated sections such as exam schedules or training duration.

## 2. Dense retrieval

Gemini embeddings provide semantic retrieval. Vectors are normalized and stored in FAISS `IndexFlatIP`.

## 3. BM25

BM25 handles exact Vietnamese names, circular numbers, dates, field codes (`748`, `74802`), school names and exam codes (`CA1`–`CA4`).

## 4. Reciprocal Rank Fusion

Dense and BM25 rankings are fused using rank-based RRF rather than pretending raw cosine and BM25 scores share one scale.

## 5. Source diversity

Before reranking, the candidate pool limits repeated chunks from one source. This helps multi-source questions retrieve both central regulation and school-specific implementation instead of letting one long document monopolize top-k.

## 6. Reranking

OpenRouter reranking is optional and failure-tolerant. If its free endpoint is unavailable, the system falls back to fused candidates instead of breaking the whole app.

## 7. OOD gate

Low-confidence questions outside VB2CA should be refused rather than answered from pretrained model memory.

---

# Evaluation

Starter benchmark:

```bash
python scripts/evaluate.py --env /content/providers.env
```

Retrieval/OOD metrics include:

- Hit@k
- Precision@k
- Recall@k
- MRR
- nDCG@k
- in-domain acceptance
- OOD rejection

Optional generation diagnostics:

```bash
python scripts/evaluate_generation.py --env /content/providers.env
```

Recommended ablations:

| Experiment | Purpose |
|---|---|
| Dense only | semantic baseline |
| BM25 only | exact-term baseline |
| Dense + BM25 + RRF | hybrid value |
| source diversity off/on | evidence breadth |
| reranker off/on | second-stage precision |
| chunk size sweep | context granularity |
| OOD threshold sweep | false accept vs false reject |
| future graph experiment | only keep if it beats the evidence-first baseline |

The project does not claim LightRAG-inspired changes improve quality until measured on the held-out benchmark.

---

# Data validation and CI

Static source governance check:

```bash
python scripts/validate_sources.py
```

Optional best-effort live reachability audit:

```bash
python scripts/validate_sources.py --live
```

CI rejects:

- non-approved source domains;
- duplicate source IDs;
- incomplete provenance metadata;
- non-A0/A1 sources in the answer registry;
- any `WATCH_ONLY_DRAFT` accidentally placed inside `data/corpus/`;
- corpus source IDs not registered as answer evidence.

GitHub Actions then runs the unit tests.

---

# Repository structure

```text
.
├── app.py
├── configs/default.yaml
├── data/
│   ├── corpus/
│   ├── source_registry.yaml
│   ├── known_source_issues.yaml
│   └── official_sources.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_GOVERNANCE.md
│   ├── DATASET.md
│   └── EVALUATION.md
├── evaluation/sample_eval.jsonl
├── notebooks/VietRAG_Colab.ipynb
├── scripts/
│   ├── ask.py
│   ├── build_index.py
│   ├── calibrate_ood.py
│   ├── evaluate.py
│   ├── evaluate_generation.py
│   └── validate_sources.py
├── src/vietrag/
│   ├── chunking.py
│   ├── config.py
│   ├── evaluation.py
│   ├── guardrails.py
│   ├── ingest.py
│   ├── persistence.py
│   ├── pipeline.py
│   ├── providers.py
│   ├── retrieval.py
│   └── secrets.py
├── tests/test_core.py
├── providers.env.example
├── SECURITY.md
├── requirements.txt
└── pyproject.toml
```

---

# Limitations

- Verification is a timestamp, not a guarantee of future validity.
- The August 2026 official draft creates a real future-change risk for admissions rules.
- 2026 quotas/deadlines must not be reused as 2027 facts.
- Public health thresholds do not replace official medical screening.
- Political-standard assessment must not be inferred beyond publicly available official guidance.
- LLM citations are constrained and sanitized, but high-stakes answers should still be checked against the linked primary source.
- Free Gemini/OpenRouter tiers may change quotas/model availability.
- Free external APIs are not appropriate for confidential internal data.

---

# Research basis

- Lewis et al., **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks** — `https://arxiv.org/abs/2005.11401`
- Robertson & Zaragoza, **BM25 and Beyond**
- RAGAS — `https://docs.ragas.io/`
- RAGChecker — `https://arxiv.org/abs/2408.08067`
- HKUDS **LightRAG** — `https://github.com/HKUDS/LightRAG`
- LightRAG paper — `https://arxiv.org/abs/2410.05779`
- Gemini Embeddings documentation — `https://ai.google.dev/gemini-api/docs/embeddings`
- OpenRouter RAG/reranking documentation — `https://openrouter.ai/docs/`

The rule for adopting a technique is simple: **if it does not improve measured retrieval/groundedness/temporal correctness, it does not belong in production.**

---

## License

MIT — see [LICENSE](LICENSE).
