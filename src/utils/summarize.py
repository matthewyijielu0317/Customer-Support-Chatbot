from __future__ import annotations

from typing import List, Dict

from src.utils.openai_client import get_openai_client


def summarize_messages(messages: List[Dict[str, str]], max_length: int = 256) -> str:
    if not messages:
        return ""

    joined = []
    for m in messages:
        role = m.get("role", "user")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        joined.append(f"{role}: {content}")

    prompt_intro = (
        "Summarize the following customer support conversation concisely. "
        "Keep key customer concerns, promises made, and next steps. "
        f"Avoid PII, and limit to {max_length} characters.\n\n"
    )
    prompt = prompt_intro + "\n".join(joined)

    client = get_openai_client()
    if client is None:
        return ""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You summarize conversations succinctly."}, {"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200,
        )
        return (resp.choices[0].message.content or "").strip()[:max_length]
    except Exception:
        return ""
