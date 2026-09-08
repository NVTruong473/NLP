# CAND-VB2 RAG — Verified Police Second-Degree Admissions Assistant 2026

> Trợ lý RAG chuyên biệt về **tuyển mới đào tạo trình độ đại học chính quy Công an nhân dân đối với công dân đã có bằng tốt nghiệp đại học trở lên (VB2CA tuyển mới)**, tập trung đặc biệt vào người có văn bằng 1 **CNTT / Computer Science / IT**.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Google Colab](https://img.shields.io/badge/Google%20Colab-Run%20All-orange)](https://colab.research.google.com/github/NVTruong473/NLP/blob/main/notebooks/VietRAG_Colab.ipynb)
[![Dataset](https://img.shields.io/badge/Dataset-Official%20sources%20only-success)](docs/DATASET.md)
[![Verified](https://img.shields.io/badge/Verified-2026--09--08-brightgreen)](data/source_registry.yaml)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## TL;DR

Clone/open the Colab notebook, upload your private API file to `/content/providers.env`, then run all cells. The project builds a local FAISS + BM25 index from **verified official-source snapshots already committed in the repository** and launches a Gradio chat app.

**External AI providers used: Gemini + OpenRouter only.**

- Gemini: embeddings + primary answer generation.
- OpenRouter: free generation fallback + optional free reranker.
- FAISS, BM25, parsing, evaluation and Gradio: local runtime code, not additional AI providers.

## Important current status — 08/09/2026

The dataset was manually cross-checked against official Ministry of Public Security and CAND-school sources on **8 September 2026**.

At that verification point:

- the Ministry of Public Security still reports the 2026 VB2CA process as active and preparing for the computer-based assessment;
- the system-wide 2026 quota is **530**;
- the Ministry reports **5,123 Method-2 applicants**;
- the assessment is scheduled for **20/09/2026**;
- the ordinary initial registration window **15/03–15/06/2026** and the **20/08/2026** file-submission milestone have already passed.

Therefore the assistant must **not** tell a person who never registered that normal 2026 registration is still open. A late/supplementary round may only be stated if a newer official notice explicitly confirms one.

---

# Why this project is different from a normal RAG demo

A naive RAG project often does:

```text
web pages → chunks → embeddings → top-k → LLM
```

That is unsafe for a time-sensitive admissions domain because old rules, unrelated “văn bằng 2” programs, and stale deadlines can be mixed together.

CAND-VB2 RAG instead uses:

```text
Official source discovery
        ↓
Authority + date + legal-status verification
        ↓
Human-reviewed factual snapshots
        ↓
Provenance metadata on every document
        ↓
Gemini dense embeddings ─┐
                         ├─> Reciprocal Rank Fusion
BM25 lexical retrieval ──┘
        ↓
OpenRouter reranking (optional/free)
        ↓
Out-of-domain / evidence-confidence gate
        ↓
Gemini grounded generation
        ↓ fallback
OpenRouter free router
        ↓
Answer + [S#] citations + official URLs + verification date
```

The goal is not to make the LLM “know about police admissions”. The goal is to make it **refuse to claim anything that the verified evidence does not support**.

---

# Exact domain boundary

This repository covers:

**VB2CA tuyển mới** = tuyển mới đào tạo đại học chính quy CAND dành cho a citizen who already has a university degree.

It deliberately distinguishes this from:

1. **văn bằng 2 dành cho cán bộ CAND đang công tác**;
2. **ordinary CAND university admission from high school/THPT**;
3. unrelated civilian second-degree programs.

Those programs can have different quotas, candidates, exam formats and timelines. The prompt contains an explicit anti-confusion rule so the model cannot merge them simply because they all contain the phrase “văn bằng 2”.

---

# The dataset

The default knowledge base is stored directly in the repository:

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
│   └── 08_scope_and_disambiguation.md
├── source_registry.yaml
└── official_sources.yaml
```

Every curated Markdown file starts with provenance such as:

```yaml
---
source_id: BCA-EXAM-2026
title: Cấu trúc Kỳ thi đánh giá VB2CA trên máy tính năm 2026
authority: Bộ Công an
official_url: https://bocongan.gov.vn/...
published: '2026-06-17'
verified_at: '2026-09-08'
status: current_for_2026_exam
scope: Kỳ thi Phương thức 2 VB2CA 2026
---
```

This metadata is preserved all the way into each retrieval chunk and shown in the final evidence list.

## Source quality policy

Only Grade-A primary sources enter the curated truth set:

- official Ministry of Public Security portal;
- official Ministry legal-document database;
- official websites of CAND academies/schools.

Not accepted as authoritative evidence:

- newspapers or news aggregators;
- SEO articles;
- coaching centers;
- Facebook/TikTok/Zalo posts not issued by the competent authority;
- forums and hearsay.

See the complete [Dataset Card](docs/DATASET.md) and [Source Registry](data/source_registry.yaml).

## Why the corpus is saved in GitHub instead of scraped every Colab run

Government sites can temporarily fail, change HTML, move attachments or update pages. If the notebook re-scraped them every run, two users could unknowingly evaluate two different datasets.

The default pipeline therefore indexes **committed, verified snapshots**. `data/official_sources.yaml` is provided only for optional live-refresh experiments.

---

# Key verified topics in the knowledge base

The corpus is specifically designed to answer questions such as:

- I already have an IT degree. Can I apply for VB2CA 2026?
- Does a `Khá` IT degree have a direct-admission route?
- Can a technical/IT graduate with a `Trung bình` degree ever satisfy the academic condition?
- What if my degree does not print a classification?
- Is field code `748` accepted?
- Can I apply to Information Security at the People’s Security Academy?
- Which schools/groups do not restrict the first-degree field for Method 2?
- Where does a resident register for preliminary screening?
- What documents are required?
- Is the 2026 registration deadline already over on 08/09/2026?
- What is the 20/09/2026 computer-based exam structure?
- What are CA1, CA2, CA3 and CA4?
- What public health thresholds apply, and what changes for an IT graduate?
- Which admissions/health regulations are still marked in force?
- How is VB2CA tuyển mới different from second-degree training for existing CAND officers?

The assistant is intentionally **not** a substitute for official preliminary screening, medical examination, political-standard assessment or a newly issued Ministry notice.

---

# Quick start on Google Colab

## Recommended: open the notebook

[Open `notebooks/VietRAG_Colab.ipynb` in Google Colab](https://colab.research.google.com/github/NVTruong473/NLP/blob/main/notebooks/VietRAG_Colab.ipynb)

Then choose **Runtime → Run all**.

The notebook automatically:

1. clones/updates this repository;
2. installs dependencies;
3. checks `/content/providers.env`;
4. asks you to upload the file if it is missing;
5. displays the verified source registry;
6. builds the local FAISS/BM25 index from `data/corpus`;
7. runs sample evidence-grounded questions;
8. tests out-of-domain refusal;
9. runs retrieval/OOD evaluation;
10. can launch the Gradio app.

## Manual Colab commands

```python
!git clone https://github.com/NVTruong473/NLP.git
%cd NLP
!pip -q install -r requirements.txt
!pip -q install -e . --no-deps
```

Then upload your key file to:

```text
/content/providers.env
```

Build the verified dataset index:

```python
!python scripts/build_index.py --input-dir data/corpus --env /content/providers.env
```

Ask one question:

```python
!python scripts/ask.py \
  "Tôi có bằng đại học CNTT loại Khá thì năm 2026 có những hướng VB2 Công an nào?" \
  --env /content/providers.env
```

Launch the app:

```python
!python app.py
```

---

# `providers.env` — keep it private

Create your own local file from `providers.env.example`:

```dotenv
GEMINI_API_KEY_1=YOUR_KEY
# GEMINI_API_KEY_2=OPTIONAL_SECOND_KEY
GEMINI_MODEL=gemini-3.8-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

OPENROUTER_API_KEY_1=YOUR_KEY
OPENROUTER_CHAT_MODEL=openrouter/free
OPENROUTER_RERANK_MODEL=nvidia/llama-nemotron-rerank-vl-1b-v2:free
```

Although the reranking model name contains `nvidia`, the application calls it **only through the OpenRouter API**. There is no NVIDIA API integration or NVIDIA key in this project.

## Why the real file is not in GitHub

This repository is public. GitHub cannot make one committed file in a public repository visible only to its owner. If `providers.env` were committed, the keys would be public and remain recoverable from Git history after ordinary deletion.

Therefore:

- `providers.env` is Git-ignored;
- only `providers.env.example` is committed;
- Colab checks `/content/providers.env` and opens an upload dialog when missing;
- key values are never printed;
- multiple Gemini/OpenRouter keys can be configured for legitimate failover/quota resilience.

If a key appears in a screenshot, public commit, notebook output or chat, revoke/rotate it.

---

# Retrieval architecture

## Dense retrieval — Gemini embeddings

`gemini-embedding-001` embeds curated documents using the retrieval-document task and questions using the question-answering task. Vectors are L2-normalized and stored in FAISS `IndexFlatIP`, making inner product equivalent to cosine similarity.

## BM25

BM25 complements semantic retrieval for exact entities that matter heavily in admissions:

- `99/2025/TT-BCA`;
- `131/2025/TT-BCA`;
- `748`, `74802`, `7480202`;
- dates such as `15/06/2026`, `20/08/2026`, `20/09/2026`;
- CA1/CA2/CA3/CA4;
- school names and abbreviations.

## Reciprocal Rank Fusion

Dense and BM25 raw scores have different scales, so the pipeline does not naively average them. It fuses ranks:

```text
RRF(d) = Σ weight_r / (k + rank_r(d))
```

## OpenRouter reranker

The fused candidate set can be reranked through OpenRouter. The configured reranker is currently a free OpenRouter endpoint. Reranking is an optimization, not a single point of failure: if it is unavailable/rate-limited, the system falls back to fused results.

## OOD/evidence gate

Before generation, top dense evidence confidence is checked. Clearly unrelated questions are refused before Gemini/OpenRouter can answer from model memory.

The threshold in `configs/default.yaml` is deliberately calibratable rather than presented as universal truth.

---

# Temporal and legal guardrails

This domain is unusually sensitive to time.

The generation prompt requires the model to:

- surface each source's `verified_at` and `status` metadata;
- state when a deadline has already passed;
- prefer current Ministry/legal-database evidence over older material;
- never invent a late/supplementary round;
- distinguish current rules from historical admissions;
- refuse when evidence is insufficient.

For legal status, the curated dataset records that at the 08/09/2026 verification point:

- `99/2025/TT-BCA`, amending admissions regulation `50/2021/TT-BCA`, is marked **Còn hiệu lực** by the Ministry legal database and effective from 06/01/2026;
- `131/2025/TT-BCA`, amending CAND special-health regulation `62/2023/TT-BCA`, is marked **Còn hiệu lực** and effective from 25/12/2025.

This is a **versioned 2026 snapshot**. Do not use it in 2027 without re-verification.

---

# Evaluation

## Retrieval + OOD

```python
!python scripts/evaluate.py --env /content/providers.env
```

The starter benchmark contains questions about:

- IT-degree eligibility;
- degree classification/GPA;
- age;
- school/major selection;
- preliminary screening and documents;
- expired deadlines/current status;
- exam structure;
- health/legal rules;
- near-domain confusion;
- unrelated OOD questions.

Metrics:

- Hit@k
- Precision@k
- Recall@k
- MRR
- nDCG@k
- in-domain acceptance rate
- OOD rejection rate
- balanced OOD accuracy

Retrieval metrics are computed over **unique source IDs**, not repeated chunks of the same document.

## Calibrate OOD

```python
!python scripts/calibrate_ood.py --env /content/providers.env
```

## Generation diagnostics

```python
!python scripts/evaluate_generation.py --env /content/providers.env
```

This optionally scores:

- faithfulness;
- answer relevancy;
- coherence;
- evidence completeness;
- citation coverage.

LLM-as-judge metrics are diagnostics, not ground truth. A serious report should add a human-reviewed held-out test set.

---

# Recommended research ablations

| Experiment | Question |
|---|---|
| Dense only | How strong is semantic retrieval alone? |
| BM25 only | How much do exact legal codes/dates help? |
| Dense + BM25 + RRF | Does hybrid retrieval improve recall? |
| Hybrid + reranker | Does second-stage ranking improve precision? |
| Different chunk sizes | What granularity best preserves rules and exceptions? |
| top-k sweep | Where does extra context become noise? |
| OOD threshold sweep | False-accept vs false-reject trade-off |
| Remove temporal snapshot | How much does explicit current-status evidence reduce stale answers? |
| Remove disambiguation document | How often does the model confuse civilian VB2CA with officer-only VB2? |

---

# Optional live-source build

The reproducible default should remain the curated corpus. To experimentally combine the snapshot with live official pages:

```python
!python scripts/build_index.py \
  --sources data/official_sources.yaml \
  --input-dir data/corpus \
  --env /content/providers.env
```

Do not publish benchmark results from a live corpus without storing its exact version/date, because web content can change.

---

# Repository structure

```text
.
├── app.py
├── configs/default.yaml
├── data/
│   ├── corpus/                    # verified 2026 snapshots
│   ├── official_sources.yaml      # optional live URLs
│   ├── source_registry.yaml       # provenance / validity registry
│   └── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATASET.md
│   └── EVALUATION.md
├── evaluation/sample_eval.jsonl
├── notebooks/VietRAG_Colab.ipynb
├── scripts/
│   ├── ask.py
│   ├── build_index.py
│   ├── calibrate_ood.py
│   ├── evaluate.py
│   └── evaluate_generation.py
├── src/vietrag/
│   ├── chunking.py
│   ├── config.py
│   ├── evaluation.py
│   ├── guardrails.py
│   ├── ingest.py
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

# Primary official evidence used

The canonical URLs and verification status live in `data/source_registry.yaml`. Major sources include:

- Ministry of Public Security — 2026 CAND admissions information:  
  https://www.bocongan.gov.vn/bai-viet/thong-tin-tuyen-sinh-cac-hoc-vien-truong-cong-an-nhan-dan-nam-2026-1773897621
- Ministry of Public Security — 2026 computer-based VB2CA sample exam/structure:  
  https://bocongan.gov.vn/bai-viet/cong-bo-de-thi-minh-hoa-ky-thi-van-bang-2-cong-an-tren-may-tinh-1781667002
- Ministry of Public Security — current organizational review dated 08/09/2026:  
  https://www.bocongan.gov.vn/bai-viet/ra-soat-cong-tac-to-chuc-ky-thi-danh-gia-tren-may-tinh-va-ban-ve-de-an-dua-tieng-anh-tro-thanh-ngon-ngu-thu-hai-trong-truong-hoc-1788850887
- Ministry legal database — `99/2025/TT-BCA`:  
  https://vanban.bocongan.gov.vn/co-so-du-lieu-van-ban/thong-tu-sua-doi-bo-sung-mot-so-dieu-cua-thong-tu-so-50-2021-tt-bca-ngay-11-5-2021-cua-bo-truong-bo-cong-an-quy-dinh-ve-tuyen-sinh-trong-cong-an-nhan-dan-1763108661?tab=attributes
- Ministry legal database — `131/2025/TT-BCA`:  
  https://vanban.bocongan.gov.vn/co-so-du-lieu-van-ban/thong-tu-sua-doi-bo-sung-mot-so-dieu-cua-thong-tu-so-62-2023-tt-bca-ngay-14-11-2023-cua-bo-truong-bo-cong-an-quy-dinh-ve-tieu-chuan-suc-khoe-dac-thu-va-kham-suc-khoe-doi-voi-luc-luong-cong-an-nhan-dan-1768967121
- Học viện Kỹ thuật và Công nghệ an ninh — VB2 2026:  
  https://hvktcnan.bocongan.gov.vn/TrangChu/tin-tuc/1966-thong-tin-tuyen-sinh-dai-hoc-van-bang-2-chinh-quy-tuyen-moi-doi-voi-nguoi-da-co-bang-tot-nghiep-trinh-do-dai-hoc-tro-len-nam-2026.html
- Học viện Cảnh sát nhân dân — VB2 tuyển mới 2026-2027:  
  https://hvcsnd.edu.vn/thong-bao-ke-hoach-tuyen-sinh-dai-hoc-van-bang-2-tuyen-moi-nam-hoc-2026-2027-13815
- Trường Đại học An ninh nhân dân — tuyển sinh 2026:  
  https://dhannd.bocongan.gov.vn/Thong-tin-tuyen-sinh/thong-bao-tuyen-sinh-tuyen-moi-dao-tao-trinh-do-dai-hoc-chinh-quy-nam-2026-a-4201
- Học viện/Trường PCCC — VB2CA 2026:  
  https://hocvienpccc.bocongan.gov.vn/blog/thong-bao-tuyen-sinh-tuyen-moi-dao-tao-trinh-do-dai-hoc-chinh-quy-cand-doi-voi-cong-dan-da-co-bang-tot-nghiep-trinh-do-dai-hoc-tro-len-nam-2026_7430

---

# Limitations

- This is a verified snapshot **as of 08/09/2026**, not a promise that no later notice will change the process.
- Political-standard assessment cannot be reduced to an LLM checklist; competent CAND authorities conduct the official assessment.
- Health figures in the corpus are public screening criteria; official medical examination decides eligibility.
- Some official appendices may contain details that are not conveniently represented in public HTML.
- The starter benchmark is useful for engineering iteration but should be expanded before making academic claims about state-of-the-art quality.
- Gemini/OpenRouter free tiers have quotas and may change availability.
- Google states Gemini API free-tier content may be used to improve products; this project therefore uses public official data by default. Do not upload confidential personal dossiers into free-tier APIs.

---

# Roadmap

- [x] verified official-source 2026 corpus
- [x] current legal-status registry
- [x] IT-first eligibility knowledge
- [x] temporal deadline guardrails
- [x] distinction between civilian VB2CA and officer-only programs
- [x] Gemini dense retrieval
- [x] BM25 + RRF hybrid retrieval
- [x] OpenRouter reranking with fallback
- [x] source provenance propagated to chunks
- [x] official URL + verification date displayed with answers
- [x] OOD refusal/calibration
- [x] retrieval + generation evaluation
- [x] Google Colab Run-All workflow
- [x] Gradio chat UI
- [ ] larger human-annotated benchmark (100–300 questions)
- [ ] automatic official-source change detection/versioning
- [ ] structured rule engine for deterministic eligibility pre-check before LLM explanation
- [ ] 2027 dataset version when official 2027 guidance is published

## License

MIT. See [LICENSE](LICENSE).
