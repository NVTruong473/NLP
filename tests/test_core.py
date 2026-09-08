from pathlib import Path

from vietrag.chunking import Chunk, Segment, chunk_segment
from vietrag.evaluation import retrieval_metrics
from vietrag.ingest import load_markdown
from vietrag.persistence import corpus_fingerprint
from vietrag.retrieval import RetrievedChunk, reciprocal_rank_fusion, source_diverse


def test_chunk_overlap_and_ids_are_stable():
    text = " ".join(f"w{i}" for i in range(100))
    seg = Segment(text=text, source="x.txt")
    a = chunk_segment(seg, chunk_words=30, overlap_words=5, min_chunk_words=5)
    b = chunk_segment(seg, chunk_words=30, overlap_words=5, min_chunk_words=5)
    assert len(a) >= 3
    assert [x.chunk_id for x in a] == [x.chunk_id for x in b]


def test_markdown_heading_boundaries_are_preserved(tmp_path: Path):
    path = tmp_path / "doc.md"
    path.write_text(
        "---\nsource_id: TEST\ntitle: Test\n---\n"
        "# Điều kiện\nNội dung điều kiện.\n"
        "## Độ tuổi\nKhông quá 30 tuổi.\n"
        "# Kỳ thi\nThi trên máy tính.\n",
        encoding="utf-8",
    )
    segments = load_markdown(path)
    sections = [s.section for s in segments]
    assert "Điều kiện" in sections
    assert "Điều kiện > Độ tuổi" in sections
    assert "Kỳ thi" in sections
    assert all(s.source == "TEST" for s in segments)


def test_rrf_prefers_consensus():
    scores = reciprocal_rank_fusion([[1, 2, 3], [2, 1, 4]], weights=[1, 1], rrf_k=60)
    assert scores[1] > scores[3]
    assert scores[2] > scores[4]


def test_source_diversity_limits_monopoly():
    def item(source: str, n: int) -> RetrievedChunk:
        return RetrievedChunk(
            chunk=Chunk(chunk_id=str(n), text="x", source=source),
            fused_score=1.0 / (n + 1),
        )

    ranked = [item("A", 0), item("A", 1), item("A", 2), item("B", 3), item("C", 4)]
    selected = source_diverse(ranked, max_per_source=2, limit=4)
    assert [x.chunk.source for x in selected] == ["A", "A", "B", "C"]


def test_retrieval_metrics():
    m = retrieval_metrics(["a", "b", "c"], {"b"}, k=3)
    assert m.hit_at_k == 1
    assert round(m.mrr, 3) == 0.5
    assert round(m.recall_at_k, 3) == 1.0


def test_index_fingerprint_changes_with_corpus(tmp_path: Path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    doc = corpus / "a.md"
    doc.write_text("alpha", encoding="utf-8")
    kwargs = {
        "chunking": {"chunk_words": 350, "overlap_words": 60, "min_chunk_words": 40},
        "embedding_model": "gemini-embedding-001",
        "embedding_dimensions": 768,
    }
    first = corpus_fingerprint([corpus], **kwargs)
    doc.write_text("beta", encoding="utf-8")
    second = corpus_fingerprint([corpus], **kwargs)
    assert first != second
