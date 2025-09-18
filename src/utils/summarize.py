from __future__ import annotations

from typing import List, Dict

from openai import OpenAI
import os

from src.config.settings import settings


_client = OpenAI(api_key=(settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")))


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

    prompt = (
        "Summarize the following customer support conversation concisely. "
        "Keep key customer concerns, promises made, and next steps. "
        "Avoid PII, and limit to {max_length} characters.\n\n"
        + "\n".join(joined)
    )

    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You summarize conversations succinctly."}, {"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200,
        )
        return (resp.choices[0].message.content or "").strip()[:max_length]
    except Exception:
        return ""

