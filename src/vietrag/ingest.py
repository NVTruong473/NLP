from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

import fitz
import requests
import yaml
from bs4 import BeautifulSoup
from docx import Document as DocxDocument

from .chunking import Segment, normalize_whitespace


DEFAULT_HEADERS = {
    "User-Agent": "VietRAG/1.1 (+https://github.com/NVTruong473/NLP)"
}


def _frontmatter(text: str) -> tuple[dict, str]:
    """Parse optional YAML frontmatter from curated Markdown snapshots."""
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, flags=re.S)
    if not match:
        return {}, text
    metadata = yaml.safe_load(match.group(1)) or {}
    return metadata if isinstance(metadata, dict) else {}, match.group(2)


def _segment_from_text(text: str, path: Path) -> Segment | None:
    metadata, body = _frontmatter(text)
    body = normalize_whitespace(body)
    if not body:
        return None
    return Segment(
        text=body,
        source=str(metadata.get("source_id") or path.stem),
        title=str(metadata.get("title") or path.stem),
        url=metadata.get("official_url") or metadata.get("url"),
        authority=metadata.get("authority"),
        published=str(metadata.get("published")) if metadata.get("published") is not None else None,
        verified_at=str(metadata.get("verified_at")) if metadata.get("verified_at") is not None else None,
        status=metadata.get("status"),
        scope=metadata.get("scope"),
    )


def load_pdf(path: str | Path) -> list[Segment]:
    path = Path(path)
    doc = fitz.open(path)
    title = (doc.metadata or {}).get("title") or path.stem
    out: list[Segment] = []
    for i, page in enumerate(doc):
        text = normalize_whitespace(page.get_text("text"))
        if text:
            out.append(Segment(text=text, source=path.stem, title=title, page=i + 1))
    return out


def load_docx(path: str | Path) -> list[Segment]:
    path = Path(path)
    doc = DocxDocument(path)
    text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return [Segment(text=normalize_whitespace(text), source=path.stem, title=path.stem)] if text.strip() else []


def load_text(path: str | Path) -> list[Segment]:
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="ignore")
    segment = _segment_from_text(raw, path)
    return [segment] if segment else []


def load_html_text(html: str, source: str, url: str | None = None) -> list[Segment]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else source
    root = soup.find("article") or soup.find("main") or soup.body or soup
    blocks: list[str] = []
    for node in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"]):
        text = normalize_whitespace(node.get_text(" ", strip=True))
        if text and (not blocks or text != blocks[-1]):
            blocks.append(text)
    content = "\n\n".join(blocks) if blocks else normalize_whitespace(root.get_text("\n", strip=True))
    return [Segment(text=content, source=source, title=title, url=url)] if content else []


def load_url(url: str, timeout: int = 30) -> list[Segment]:
    r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    r.raise_for_status()
    ctype = r.headers.get("content-type", "").lower()
    name = Path(urlparse(url).path).name or urlparse(url).netloc
    if "pdf" in ctype or name.lower().endswith(".pdf"):
        tmp = Path("/tmp") / (name or "document.pdf")
        tmp.write_bytes(r.content)
        segments = load_pdf(tmp)
        for s in segments:
            s.url = url
            s.source = Path(name).stem or url
        return segments
    return load_html_text(r.text, source=name or url, url=url)


def load_path(path: str | Path) -> list[Segment]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix == ".docx":
        return load_docx(path)
    if suffix in {".txt", ".md", ".csv", ".json"}:
        return load_text(path)
    if suffix in {".html", ".htm"}:
        return load_html_text(path.read_text(encoding="utf-8", errors="ignore"), source=path.stem)
    mime = mimetypes.guess_type(path.name)[0] or ""
    raise ValueError(f"Unsupported file type: {path} ({mime})")
