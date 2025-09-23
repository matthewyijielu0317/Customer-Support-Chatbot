from __future__ import annotations

import re
from typing import List, Iterable

from langchain.schema import Document


HEADER_FOOTER_MAX_LINES = 2


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\u00AD", "")  # soft hyphen
    # fix hyphenation at line breaks: "exam-\nple" -> "example"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # collapse multiple newlines but preserve paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    # collapse internal whitespace sequences
    text = re.sub(r"[ \t\x0b\x0c\r]+", " ", text)
    # trim spaces around newlines
    text = re.sub(r" *\n *", "\n", text)
    # replace remaining newlines with spaces
    text = text.replace("\n", " ")
    # clean up multiple spaces that may result from newline replacement
    text = re.sub(r" +", " ", text)
    return text.strip()


def _detect_repeated_lines(pages: List[str]) -> set[str]:
    """Find header/footer lines that repeat across many pages."""
    counts: dict[str, int] = {}
    for page in pages:
        lines = [l.strip() for l in page.splitlines() if l.strip()]
        if not lines:
            continue
        head = lines[:HEADER_FOOTER_MAX_LINES]
        foot = lines[-HEADER_FOOTER_MAX_LINES:]
        for l in head + foot:
            counts[l] = counts.get(l, 0) + 1

    repeated = {l for l, c in counts.items() if c >= max(2, len(pages) // 3)}
    return repeated


def _remove_headers_footers(page_text: str, repeated_lines: set[str]) -> str:
    lines = [l for l in page_text.splitlines()]
    # remove matching lines at page edges only
    for i in range(min(HEADER_FOOTER_MAX_LINES, len(lines))):
        if lines and lines[0].strip() in repeated_lines:
            lines.pop(0)
    for i in range(min(HEADER_FOOTER_MAX_LINES, len(lines))):
        if lines and lines[-1].strip() in repeated_lines:
            lines.pop()
    return "\n".join(lines)


def preprocess_documents(documents: Iterable[Document]) -> List[Document]:
    """Clean PDF-derived Documents while preserving metadata.

    Steps:
    - Remove repeated headers/footers across pages
    - De-hyphenate line-break hyphenation and normalize whitespace
    - Drop control chars and redundant blank lines
    """
    docs = list(documents)
    if not docs:
        return []

    # Group by source (PDF) to detect headers/footers per file
    by_source: dict[str, List[Document]] = {}
    for d in docs:
        src = str((d.metadata or {}).get("source", "unknown"))
        by_source.setdefault(src, []).append(d)

    cleaned: List[Document] = []
    for src, group in by_source.items():
        pages = [g.page_content for g in group]
        repeated = _detect_repeated_lines(pages)
        for g in group:
            text = _remove_headers_footers(g.page_content, repeated)
            text = _normalize_whitespace(text)
            cleaned.append(Document(page_content=text, metadata=g.metadata))

    return cleaned


