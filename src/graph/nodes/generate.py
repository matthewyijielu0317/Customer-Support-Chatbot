from __future__ import annotations

from typing import List, Sequence, Any, Optional

from openai import OpenAI
import os

from src.config.settings import settings
from src.graph.state import RAGState, Citation


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
    sql_rows = state.sql_rows or []
    order_rows = [row for row in sql_rows if isinstance(row, dict) and "order_id" in row]
    session_summary = (state.session_summary or "").strip()
    recent_messages = state.recent_messages or []

    def _mask_email(email: str) -> str:
        try:
            local, domain = (email or "").split("@", 1)
            if not local or not domain:
                return "[redacted]"
            masked_local = (local[0] + "***") if len(local) > 1 else "*"
            masked_domain = "***.***"
            return f"{masked_local}@{masked_domain}"
        except Exception:
            return "[redacted]"

    def _format_sql(rows: List[dict]) -> str:
        if not rows:
            return "[no database facts]"
        out: List[str] = []
        for r in rows[:5]:
            # Render common shapes
            if "order_id" in r:
                out.append(
                    (
                        f"Order #{r.get('order_id')} — customer_email: {_mask_email(str(r.get('customer_email') or ''))}, "
                        f"product: {r.get('product_name')}, qty: {r.get('quantity')}, "
                        f"order_date: {r.get('order_date')}, delivery_date: {r.get('delivery_date')}"
                    ).strip()
                )
            elif "customer_id" in r:
                out.append(
                    (
                        f"Customer #{r.get('customer_id')} — email: {_mask_email(str(r.get('email') or ''))}"
                    ).strip()
                )
            elif "product_id" in r:
                out.append(
                    (
                        f"Product #{r.get('product_id')} — {r.get('product_name')} ({r.get('product_category')}), "
                        f"unit_price: {r.get('unit_price')}"
                    ).strip()
                )
        return "\n".join(out)

    def _format_recent(messages: Sequence[dict]) -> str:
        if not messages:
            return "[no recent conversation]"
        parts: List[str] = []
        for m in messages[-settings.recent_messages_window :]:
            role = m.get("role", "user")
            content = (m.get("content") or "").strip()
            if not content:
                continue
            parts.append(f"{role}: {content}")
        return "\n".join(parts) if parts else "[no recent conversation]"

    system_prompt = (
        "You are a helpful, concise customer support assistant for an e-commerce company. "
        "Use DATABASE FACTS as authoritative for any order/customer/product details. "
        "Use POLICY CONTEXT for rules and procedures. If identifiers are missing, ask one concise clarifying question. "
        "PRIVACY: Never disclose personal data (emails, addresses, names, phone) that the user did not explicitly provide. "
        "If there is a mismatch between provided identifiers and database values, DO NOT reveal the database values; instead ask the user to verify or provide correct information. "
        "When referencing any email or personal data, use a redacted form (e.g., v***@***.***) unless the user provided the exact same value. "
        "If the answer is not clearly supported by the database facts or policy context, say you are not sure and "
        "briefly state what information is missing or suggest next steps. Be succinct."
    )

    feedback = (state.grounded_explanation or "").strip() if state.grounded is False else ""
    feedback_block = f"\n\nGroundedness feedback: {feedback}\nPlease revise to be strictly supported by the context above." if feedback else ""

    if order_rows:
        state.answer = _format_order_response(order_rows)
        state.should_retrieve = False
        return state

    user_prompt = (
        f"User intent: {intent}.\n"
        f"User question: {state.query}\n\n"
        f"Session summary: {session_summary if session_summary else '[no prior summary]'}\n\n"
        f"Recent conversation:\n{_format_recent(recent_messages)}\n\n"
        f"Database facts (authoritative, concise):\n{_format_sql(sql_rows)}\n\n"
        f"Policy context sections (may be partial and noisy):\n{context if context else '[no retrieved context]'}{feedback_block}\n\n"
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

    if (
        getattr(state, "should_cache", False)
        and not getattr(state, "cache_hit", False)
        and state.cache_key
        and getattr(state, "semantic_cache", None)
        and state.user_id
    ):
        cache = state.semantic_cache
        citations_payload: List[dict] = []
        for citation in state.citations or []:
            if isinstance(citation, Citation):
                citations_payload.append(citation.model_dump())
            elif isinstance(citation, dict):
                citations_payload.append(citation)
        cache_payload = {
            "answer": state.answer,
            "citations": citations_payload,
            "intent": state.intent,
            "trace_id": state.trace_id,
            "metadata": {"session_id": state.session_id},
        }

        cache.upsert(
            state.cache_key,
            cache_payload,
            query=state.query,
        )

    return state


def _format_order_response(order_rows: List[dict]) -> str:
    lines: List[str] = []
    for order in order_rows:
        order_id = order.get("order_id")
        product = order.get("product_name") or "item"
        quantity = order.get("quantity")
        order_date = _format_date(order.get("order_date"))
        delivery_date = _format_date(order.get("delivery_date"))

        parts: List[str] = []
        if quantity:
            parts.append(f"{quantity} x {product}")
        else:
            parts.append(str(product))
        if order_date:
            parts.append(f"ordered on {order_date}")
        if delivery_date:
            parts.append(f"delivery {delivery_date}")

        description = ", ".join(parts)
        if order_id is not None:
            lines.append(f"Order #{order_id}: {description}.")
        else:
            lines.append(description)

    if not lines:
        return "I found your order details, but I could not format them right now."

    if len(lines) == 1:
        return "Here is your order detail:\n" + lines[0]
    return "Here are your order details:\n" + "\n".join(f"- {line}" for line in lines)


def _format_date(value: Any) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, str):
        return value
    try:
        return value.isoformat()
    except AttributeError:
        return str(value)
