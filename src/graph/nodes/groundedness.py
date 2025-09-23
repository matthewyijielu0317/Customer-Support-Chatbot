from __future__ import annotations

from src.graph.state import RAGState
from src.utils.text import format_context_sections
from src.utils.openai_client import get_openai_client


def groundedness_node(state: RAGState) -> RAGState:
    # If we have no document context, skip checking
    if not state.docs:
        state.grounded = None
        state.grounded_explanation = None
        return state

    context = format_context_sections(state.docs or [])
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

    client = get_openai_client()
    try:
        if client is None:
            raise RuntimeError("OpenAI client is not configured")
        resp = client.chat.completions.create(
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
