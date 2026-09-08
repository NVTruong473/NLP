# Evaluation protocol

A RAG system should not be evaluated with one global score. Retrieval and generation fail in different ways, so VietRAG evaluates them separately.

## 1. Retrieval

Implemented in `src/vietrag/evaluation.py` and `scripts/evaluate.py`:

- **Hit@k** — whether at least one relevant source appears in top-k.
- **Precision@k** — fraction of top-k results that are relevant.
- **Recall@k** — fraction of known relevant sources recovered.
- **MRR** — rewards placing the first relevant result high in the ranking.
- **nDCG@k** — ranking quality with logarithmic discount.

## 2. Domain / OOD refusal

The current production guard uses top dense cosine similarity. Do not treat the default threshold as universal. Create a labeled set containing both answerable and out-of-domain questions, then calibrate the threshold with `scripts/calibrate_ood.py`.

Recommended report:

- in-domain acceptance rate
- out-of-domain rejection rate
- balanced accuracy
- false-accept examples
- false-reject examples

## 3. Generation

Recommended metrics:

- **Faithfulness / groundedness**: claims supported by retrieved evidence.
- **Answer relevancy**: response addresses the question.
- **Citation coverage**: factual statements include `[S#]` citations.
- **Completeness**: important evidence-backed parts of the answer are not omitted.
- **Coherence**: response is logically organized and readable.

For a formal experiment, pair automated LLM-as-judge scoring with a small human-rated set. Automated metrics are useful for iteration but should not be presented as an unquestionable ground truth.

## 4. Ablations worth reporting

Run the same benchmark under:

1. dense only
2. BM25 only
3. dense + BM25 + RRF
4. hybrid + rerank
5. different chunk sizes
6. different top-k values
7. different OOD thresholds

The goal is to show *why* each component exists rather than adding components because they sound advanced.

## Research references

- Lewis et al. (2020), *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*.
- RAGAS: systematic component-level evaluation for RAG applications.
- Ru et al. (2024), *RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented Generation*.
- Robertson & Zaragoza (2009), *The Probabilistic Relevance Framework: BM25 and Beyond*.

See the main README for links.
