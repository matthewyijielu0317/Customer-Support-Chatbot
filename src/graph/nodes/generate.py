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


def generate_node(state: RAGState) -> RAGState:
    intent = state.intent or "policy_qna"
    context = _format_context(state.docs or [])

    system_prompt = (
        "You are a helpful, concise customer support assistant for an e-commerce company. "
        "Use the provided context sections to answer the user's question. "
        "If the answer is not clearly supported by the context, say you are not sure and "
        "briefly state what information is missing or suggest next steps. Be succinct."
    )

    feedback = (state.grounded_explanation or "").strip() if state.grounded is False else ""
    feedback_block = f"\n\nGroundedness feedback: {feedback}\nPlease revise to be strictly supported by the context above." if feedback else ""

    user_prompt = (
        f"User intent: {intent}.\n"
        f"User question: {state.query}\n\n"
        f"Context sections (may be partial and noisy):\n{context if context else '[no retrieved context]'}{feedback_block}\n\n"
        "Answer:"
    )

    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=400,
        )
        content = resp.choices[0].message.content or ""
        state.answer = content.strip()
        # Increment retry counter if we just produced a revised answer after a failed groundedness
        if feedback:
            state.grounded_retry_count = (state.grounded_retry_count or 0) + 1
    except Exception as exc:
        state.answer = f"Failed to generate answer: {exc}"

    return state


