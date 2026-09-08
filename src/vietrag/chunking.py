from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass
class Segment:
    text: str
    source: str
    title: str = ""
    page: int | None = None
    url: str | None = None
    authority: str | None = None
    published: str | None = None
    verified_at: str | None = None
    status: str | None = None
    scope: str | None = None
    section: str | None = None
    evidence_grade: str | None = None
    temporal_class: str | None = None
    change_risk: str | None = None


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str
    title: str = ""
    page: int | None = None
    url: str | None = None
    authority: str | None = None
    published: str | None = None
    verified_at: str | None = None
    status: str | None = None
    scope: str | None = None
    section: str | None = None
    evidence_grade: str | None = None
    temporal_class: str | None = None
    change_risk: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[\t\r ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _id_for(segment: Segment, start_word: int, text: str) -> str:
    raw = (
        f"{segment.source}|{segment.page}|{segment.section}|{start_word}|{text[:120]}"
    ).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def _chunk_from_segment(segment: Segment, start_word: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=_id_for(segment, start_word, text),
        text=text,
        source=segment.source,
        title=segment.title,
        page=segment.page,
        url=segment.url,
        authority=segment.authority,
        published=segment.published,
        verified_at=segment.verified_at,
        status=segment.status,
        scope=segment.scope,
        section=segment.section,
        evidence_grade=segment.evidence_grade,
        temporal_class=segment.temporal_class,
        change_risk=segment.change_risk,
    )


def chunk_segment(
    segment: Segment,
    chunk_words: int = 350,
    overlap_words: int = 60,
    min_chunk_words: int = 40,
) -> list[Chunk]:
    """Chunk within one semantic section.

    Markdown heading boundaries are created upstream by ``ingest.load_markdown``.
    This avoids mixing unrelated legal/admissions sections merely because a
    fixed token window crossed a heading boundary.
    """
    text = normalize_whitespace(segment.text)
    words = text.split()
    if not words:
        return []
    if len(words) <= chunk_words:
        return [_chunk_from_segment(segment, 0, text)]

    step = max(1, chunk_words - overlap_words)
    chunks: list[Chunk] = []
    for start in range(0, len(words), step):
        part = words[start : start + chunk_words]
        if len(part) < min_chunk_words and chunks:
            # Keep tail information, but never merge across a heading/segment.
            chunks[-1].text = f"{chunks[-1].text} {' '.join(part)}".strip()
            break
        chunk_text = " ".join(part)
        chunks.append(_chunk_from_segment(segment, start, chunk_text))
        if start + chunk_words >= len(words):
            break
    return chunks


def chunk_segments(segments: Iterable[Segment], **kwargs) -> list[Chunk]:
    output: list[Chunk] = []
    for segment in segments:
        output.extend(chunk_segment(segment, **kwargs))
    return output
