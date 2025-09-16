from __future__ import annotations

from typing import List

from openai import OpenAI
import os

from src.config.settings import settings
from src.graph.state import RAGState


_client = OpenAI(api_key=(settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")))


def _format_context(docs: List[dict]) -> str:
    lines: List[str] = []
    for i, d in enumerate(docs, start=1):
        title = d.get("title") or ""
        source = d.get("source") or ""
        page = d.get("page")
        header = f"[{i}] {title} — {source}".strip()
        if page is not None:
            header += f" (p.{page})"
        text = (d.get("text") or "").strip()
        if text:
            lines.append(header + "\n" + text)
    return "\n\n".join(lines)


def groundedness_node(state: RAGState) -> RAGState:
    # If we didn't retrieve, skip checking
    if not state.should_retrieve:
        state.grounded = None
        state.grounded_explanation = None
        return state

    context = _format_context(state.docs or [])
    answer = (state.answer or "").strip()
    if not answer:
        state.grounded = False
        state.grounded_explanation = "No answer to verify."
        return state

    system = (
        "You are a strict groundedness judge.\n"
        "Given the retrieved context sections and the assistant's answer, determine if the answer is directly supported by the context.\n"
        "Only return one of: GROUNDED or NOT_GROUNDED and then a short reason."
    )
    user = (
        f"Context:\n{context if context else '[no context]'}\n\n"
        f"Answer:\n{answer}\n\n"
        "Respond in the format: <VERDICT> - <short reason>."
    )

    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            max_tokens=60,
        )
        content = (resp.choices[0].message.content or "").strip().upper()
        grounded = content.startswith("GROUNDED") and not content.startswith("NOT_GROUNDED")
        state.grounded = bool(grounded)
        state.grounded_explanation = content
    except Exception as exc:
        state.grounded = None
        state.grounded_explanation = f"Groundedness judge failed: {exc}"

    return state


