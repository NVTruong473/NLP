# VietRAG — Evidence-First RAG for Vietnamese Institutional Knowledge

> A personal NLP/LLM project that turns specialized documents into a grounded question-answering system with hybrid retrieval, out-of-domain refusal, source citations, evaluation, and a Colab-first demo.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Colab](https://img.shields.io/badge/Google%20Colab-ready-orange)](https://colab.research.google.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## Why this project exists

Many RAG demos stop at **chunk → vector search → top-k → LLM**. That is not enough for institutional or specialized knowledge: the system must know when it does **not** have evidence, preserve source metadata, retrieve both semantic and exact lexical matches, and expose measurable failure modes.

VietRAG is built around that stricter requirement:

- answers are grounded only in indexed documents;
- factual claims are accompanied by `[S#]` citations;
- clearly out-of-domain questions are rejected instead of answered from model memory;
- dense retrieval and BM25 are fused before generation;
- reranking is optional and failure-tolerant;
- retrieval and refusal behavior are evaluated separately;
- API keys and private documents are never committed.

The default reproducible demo uses **public TDTU admissions and undergraduate-regulation pages**. The engine itself is domain-agnostic: replace those sources with internal policies, procedures, manuals, legal documents, product knowledge, finance documents, or another specialized corpus.

---

## Architecture

```text
PDF / DOCX / TXT / HTML / explicit URLs
                  │
                  ▼
        extraction + metadata
                  │
                  ▼
       overlapping text chunks
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
 Gemini Embeddings         BM25
  semantic search        exact terms
        │                   │
        └─────────┬─────────┘
                  ▼
        Reciprocal Rank Fusion
                  │
                  ▼
 OpenRouter rerank (optional/free)
                  │
                  ▼
       retrieval-confidence gate
           ┌──────┴───────┐
         refuse         answerable
                           │
                           ▼
                  grounded generation
                  Gemini → OpenRouter
                       fallback
                           │
                           ▼
                  answer + citations
```

Only **Gemini** and **OpenRouter** are used as external AI APIs. FAISS, BM25, document parsing and Gradio run locally in the Colab/runtime.

See [Architecture](docs/ARCHITECTURE.md) for design rationale.

---

## Core stack

| Layer | Choice | Why |
|---|---|---|
| Primary LLM | `gemini-3.8-flash` | Current Gemini Flash model, strong quality/speed and available on Gemini API free tier at the time of this project |
| Fallback LLM | `openrouter/free` | Automatically routes to an available free OpenRouter model |
| Embeddings | `gemini-embedding-001` | Free-tier text embedding model with retrieval task types |
| Dense index | FAISS `IndexFlatIP` | Simple, exact cosine search after L2 normalization; ideal for Colab-scale experiments |
| Lexical retrieval | BM25 | Recovers exact codes, dates, names and regulation terminology |
| Fusion | Reciprocal Rank Fusion | Combines rankings without pretending raw BM25 and cosine scores share a scale |
| Reranking | OpenRouter `/rerank` | Improves precision on a small candidate set; optional fallback behavior if unavailable |
| UI | Gradio | One-command interactive demo in Colab |
| Evaluation | Hit@k, Precision@k, Recall@k, MRR, nDCG@k, OOD rejection | Separates retrieval quality from domain-refusal behavior |

All model names are configurable in `providers.env`; the code does not hard-code a paid model dependency.

---

# Run on Google Colab

The recommended entry point is:

**`notebooks/VietRAG_Colab.ipynb`**

### 1. Clone the repository

```bash
!git clone https://github.com/NVTruong473/NLP.git
%cd NLP
```

### 2. Install dependencies

```bash
!pip install -q -r requirements.txt
!pip install -q -e . --no-deps
```

### 3. Provide API keys safely

Create a local file named `providers.env` using [providers.env.example](providers.env.example):

```dotenv
GEMINI_API_KEY_1=YOUR_KEY
GEMINI_API_KEY_2=ANOTHER_KEY_IF_NEEDED
GEMINI_MODEL=gemini-3.8-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

OPENROUTER_API_KEY_1=YOUR_KEY
OPENROUTER_CHAT_MODEL=openrouter/free
OPENROUTER_RERANK_MODEL=nvidia/llama-nemotron-rerank-vl-1b-v2:free
```

Then upload it to the Colab runtime as:

```text
/content/providers.env
```

The notebook checks for `/content/providers.env`. If the file is missing it opens the Colab upload dialog. **It deliberately does not download this file from GitHub.**

### Why not store `providers.env` in this public repo?

Because GitHub has no feature that makes one committed file inside a **public repository** visible only to the owner. Committing the file would expose the keys to anyone who can read the repository, including through Git history after later deletion.

The repository therefore contains only `providers.env.example`, while `.gitignore` blocks `providers.env` and `*.env`.

See [SECURITY.md](SECURITY.md).

### 4. Build the demo index

```bash
!python scripts/build_index.py \
  --sources data/demo_sources.yaml \
  --env /content/providers.env
```

The demo pulls only explicitly listed official public pages, extracts their text, creates chunks, embeds them with Gemini, and stores the FAISS index under `artifacts/index/`.

### 5. Ask a question

```bash
!python scripts/ask.py \
  "TDTU có những phương thức tuyển sinh đại học nào trong năm 2026?" \
  --env /content/providers.env
```

### 6. Launch the web UI

```bash
!python app.py
```

Gradio returns a temporary share link in Colab.

---

# Use your own documents

Upload files into:

```text
data/uploads/
```

Then build an index without the public demo sources:

```bash
!python scripts/build_index.py \
  --sources "" \
  --input-dir data/uploads \
  --env /content/providers.env
```

Supported formats:

- text-based `.pdf`
- `.docx`
- `.txt` / `.md`
- `.html` / `.htm`
- explicit HTTP/HTTPS URLs in a YAML source list

`data/uploads/` is Git-ignored so local/private documents are not accidentally committed.

> Scanned PDFs that contain only images are not silently OCR'd in v1. A robust product should measure OCR quality separately rather than pretending empty extraction is valid text.

---

# Repository structure

```text
.
├── app.py                         # Gradio app
├── configs/
│   └── default.yaml               # Chunking/retrieval/generation settings
├── data/
│   ├── README.md
│   └── demo_sources.yaml          # Public reproducible demo corpus
├── docs/
│   ├── ARCHITECTURE.md
│   └── EVALUATION.md
├── evaluation/
│   └── sample_eval.jsonl          # Small starter benchmark
├── notebooks/
│   └── VietRAG_Colab.ipynb        # End-to-end Colab workflow
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
├── tests/
│   └── test_core.py
├── providers.env.example
├── SECURITY.md
├── requirements.txt
└── pyproject.toml
```

---

# How retrieval works

## 1. Dense semantic retrieval

Documents are embedded with Gemini using a retrieval-document task; questions use a question-answering retrieval task. Embeddings are L2-normalized and searched with FAISS inner product, which becomes cosine similarity after normalization.

## 2. BM25 lexical retrieval

BM25 runs over Unicode-aware lower-cased tokens. It complements dense search for details such as:

- decision numbers;
- dates;
- course/program names;
- abbreviations;
- exact Vietnamese legal/academic phrases.

## 3. Reciprocal Rank Fusion

Instead of min-max scaling incomparable raw scores, VietRAG fuses **ranks**:

```text
RRF(d) = Σ weight_r / (k + rank_r(d))
```

This is intentionally simple, robust and easy to ablate.

## 4. Reranking

The fused candidate set can be sent to OpenRouter's rerank endpoint. If the configured free reranker is unavailable or rate-limited, the request does **not** crash the RAG system: it falls back to top fused results.

## 5. Domain/OOD gate

A specialized RAG assistant should not answer an unrelated question merely because Gemini or an OpenRouter model knows the answer. VietRAG checks retrieval confidence before generation and refuses low-confidence queries.

The default threshold in `configs/default.yaml` is a starting value, **not a universal truth**. Use the calibration script on your own labeled queries:

```bash
!python scripts/calibrate_ood.py --env /content/providers.env
```

Then update:

```yaml
retrieval:
  ood_dense_threshold: YOUR_CALIBRATED_VALUE
```

---

# Evaluation

Run the starter retrieval/OOD benchmark:

```bash
!python scripts/evaluate.py --env /content/providers.env
```

Reported retrieval/OOD metrics:

- Hit@k
- Precision@k
- Recall@k
- MRR
- nDCG@k
- OOD rejection accuracy

For optional LLM-as-judge diagnostics (faithfulness, answer relevancy, coherence, evidence completeness and citation coverage):

```bash
!python scripts/evaluate_generation.py --env /content/providers.env
```

For a serious report, expand `evaluation/sample_eval.jsonl` into a held-out benchmark with multiple question types, difficult paraphrases, exact-lookup questions, multi-hop questions, and adversarial/out-of-domain questions.

Recommended ablations:

| Experiment | What it tests |
|---|---|
| Dense only | semantic retriever baseline |
| BM25 only | lexical baseline |
| Dense + BM25 + RRF | value of hybrid retrieval |
| Hybrid + reranker | value of second-stage ranking |
| chunk size sweep | context granularity vs recall |
| top-k sweep | recall vs context noise |
| OOD threshold sweep | false accept vs false reject trade-off |

See [Evaluation protocol](docs/EVALUATION.md).

---

# API key rotation

`GEMINI_API_KEY_1...N` and `OPENROUTER_API_KEY_1...N` are supported. The provider layer rotates to another configured key when one key encounters an API/rate-limit failure.

The application prints only the **number** of loaded keys, never the values.

This is a resiliency mechanism for legitimate quotas; it is not intended to bypass provider terms or restrictions.

---

# Free-tier strategy

This project is designed to be usable without a paid inference server:

1. Gemini is the primary LLM and embedding provider.
2. OpenRouter uses `openrouter/free` as the generation fallback.
3. Reranking is optional and must fail gracefully.
4. FAISS/BM25/document extraction run locally in Colab.
5. Index artifacts are persisted locally for the session so documents are not re-embedded for every question.

Free tiers and model availability can change. Treat model names as configuration, not permanent assumptions.

---

# Security checklist

Before pushing changes:

```bash
git status
git grep -nE "(GEMINI_API_KEY|OPENROUTER_API_KEY).*=" -- ':!providers.env.example'
```

Confirm that:

- `providers.env` is not tracked;
- private documents are not tracked;
- generated indexes are not tracked;
- screenshots/logs do not contain keys.

If an API key ever appears in a public screenshot, chat, commit or log, rotate/revoke it immediately.

---

# Research basis

This implementation intentionally borrows ideas from established retrieval/RAG work rather than adding fashionable components without a measurable role:

- **Retrieval-Augmented Generation** — Lewis et al., 2020: https://arxiv.org/abs/2005.11401
- **BM25 and probabilistic relevance** — Robertson & Zaragoza, 2009: https://doi.org/10.1561/1500000019
- **RAGAS** — component-level RAG evaluation: https://docs.ragas.io/
- **RAGChecker** — fine-grained retrieval/generation diagnostics: https://arxiv.org/abs/2408.08067
- **Gemini Embeddings** — retrieval-oriented embedding task types: https://ai.google.dev/gemini-api/docs/embeddings
- **OpenRouter RAG / rerank API** — embeddings, reranking and chat pipeline patterns: https://openrouter.ai/docs/guides/evaluate-and-optimize/rag

The project does not claim that an architecture is superior until it is tested on the target corpus. The evaluation and ablation structure exists specifically to challenge that assumption.

---

# Limitations

- The starter demo corpus is small and public; it is not a production knowledge base.
- Retrieval-confidence thresholds require domain-specific calibration.
- LLM citations are constrained by prompting but should still be audited in high-stakes deployments.
- HTML extraction is generic and may include boilerplate on unusual sites.
- OCR and table-aware multimodal parsing are intentionally deferred until they can be evaluated properly.
- Free API quotas and free model availability can change over time.

---

# Roadmap

- [x] Gemini + OpenRouter provider abstraction with key rotation
- [x] PDF/DOCX/TXT/HTML/URL ingestion
- [x] Gemini dense embeddings + FAISS
- [x] BM25 + Reciprocal Rank Fusion
- [x] OpenRouter reranking with graceful fallback
- [x] OOD refusal gate
- [x] inline source citations
- [x] retrieval/OOD evaluation
- [x] threshold calibration
- [x] Colab + Gradio demo
- [ ] query decomposition for genuinely multi-hop questions
- [ ] table-aware extraction benchmark
- [ ] multimodal scanned-PDF ingestion benchmark
- [ ] human-evaluated Vietnamese benchmark
- [ ] persistent vector database adapter for larger deployments
- [ ] observability dashboard for latency, quota and retrieval failure analysis

---

## License

MIT. See [LICENSE](LICENSE).
