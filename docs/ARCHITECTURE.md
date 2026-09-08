# Architecture

## Design goal

VietRAG is intentionally designed as an **evidence-first system**, not a demo that simply concatenates top-k chunks into a prompt.

The system must be able to answer three questions for every response:

1. **Why was this evidence retrieved?**
2. **Is there enough evidence to answer at all?**
3. **Which source supports each factual claim?**

## Pipeline

```text
PDF / DOCX / TXT / HTML / official URLs
                  │
                  ▼
        structure-preserving extraction
                  │
                  ▼
      overlapping semantic-ish chunks
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
Gemini embeddings         BM25
(dense semantic)       (lexical exact)
        │                   │
        └─────────┬─────────┘
                  ▼
        Reciprocal Rank Fusion
                  │
                  ▼
   OpenRouter rerank (optional/free)
                  │
                  ▼
       retrieval confidence gate
          ┌───────┴────────┐
       insufficient       sufficient
          │                  │
          ▼                  ▼
        refuse      grounded generation
                     Gemini → OpenRouter
                         fallback
                          │
                          ▼
                    inline citations
```

## Why hybrid retrieval?

Dense retrieval handles paraphrases and semantic matching. BM25 remains strong for exact terms such as regulation numbers, course names, codes, dates, acronyms, and Vietnamese proper nouns. Reciprocal Rank Fusion combines the two without assuming their raw scores are on the same scale.

## Why reranking?

First-stage retrieval optimizes recall. Reranking optimizes precision on a much smaller candidate set. VietRAG uses the OpenRouter rerank endpoint when available; failure is non-fatal and the system falls back to fused retrieval.

## Why a refusal gate?

A specialized institutional assistant should not answer arbitrary questions merely because the LLM knows the answer from pretraining. The retrieval score gate rejects clearly out-of-domain questions before generation. The generation prompt adds a second evidence sufficiency check.

The default threshold is only a starting point. A real deployment should run `scripts/calibrate_ood.py` on labeled in-domain and out-of-domain queries and then update `configs/default.yaml`.

## Provider policy

Only two external AI providers are used:

- **Gemini**: primary generation + document/query embeddings.
- **OpenRouter**: free-model generation fallback + optional reranking.

FAISS, BM25, PyMuPDF, BeautifulSoup and Gradio run locally in the Colab/runtime and are not AI provider APIs.
