from vietrag.chunking import Segment, chunk_segment
from vietrag.evaluation import retrieval_metrics
from vietrag.retrieval import reciprocal_rank_fusion


def test_chunk_overlap_and_ids_are_stable():
    text = " ".join(f"w{i}" for i in range(100))
    seg = Segment(text=text, source="x.txt")
    a = chunk_segment(seg, chunk_words=30, overlap_words=5, min_chunk_words=5)
    b = chunk_segment(seg, chunk_words=30, overlap_words=5, min_chunk_words=5)
    assert len(a) >= 3
    assert [x.chunk_id for x in a] == [x.chunk_id for x in b]


def test_rrf_prefers_consensus():
    scores = reciprocal_rank_fusion([[1, 2, 3], [2, 1, 4]], weights=[1, 1], rrf_k=60)
    assert scores[1] > scores[3]
    assert scores[2] > scores[4]


def test_retrieval_metrics():
    m = retrieval_metrics(["a", "b", "c"], {"b"}, k=3)
    assert m.hit_at_k == 1
    assert round(m.mrr, 3) == 0.5
    assert round(m.recall_at_k, 3) == 1.0
