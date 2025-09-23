"""Text processing and formatting utilities."""

from __future__ import annotations

import re
from typing import Mapping, Sequence


def normalize_query(q: str) -> str:
    """Normalize a query string by trimming and collapsing whitespace."""
    q = q.strip().lower()
    q = re.sub(r"\s+", " ", q)
    return q


def format_context_sections(docs: Sequence[Mapping[str, object]]) -> str:
    """Render retrieved document chunks into a numbered context block.
    
    Args:
        docs: Sequence of document dictionaries with title, source, page, text fields
        
    Returns:
        Formatted string with numbered sections
    """
    lines: list[str] = []
    for idx, doc in enumerate(docs, start=1):
        title = str(doc.get("title") or "")
        source = str(doc.get("source") or "")
        page = doc.get("page")
        header = f"[{idx}] {title} — {source}".strip()
        if page is not None:
            header = f"{header} (p.{page})"
        text = str(doc.get("text") or "").strip()
        if text:
            lines.append(f"{header}\n{text}")
    return "\n\n".join(lines)

