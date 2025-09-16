from __future__ import annotations

from typing import Literal

from openai import OpenAI
import os

from src.config.settings import settings
from src.graph.state import RAGState


IntentType = Literal[
    "payments_billing",
    "returns_exchanges",
    "shipping_delivery",
    "order_management",
    "customer_account",
    "product_information",
    "chitchat",
]


_client = OpenAI(api_key=(settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")))


def _classify_intent_llm(query: str) -> str | None:
    labels = (
        "payments_billing | returns_exchanges | shipping_delivery | order_management | "
        "customer_account | product_information | chitchat"
    )
    system = (
        "You classify customer queries into one of a fixed set of intents. "
        "Choose the single most relevant label and reply with ONLY that label."
    )
    user = (
        "Categories: payments_billing (payments, billing, refunds policy scope), returns_exchanges (return windows, exchanges), "
        "shipping_delivery (shipping methods, delivery timing), order_management (order status, cancellations, modifications), "
        "customer_account (login, password, profile, addresses), product_information (product details, specs, availability), chitchat (greetings, small talk).\n"
        f"Valid labels: {labels}.\n"
        f"Query: {query}\n"
        "Answer with ONE label from the list exactly."
    )
    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            max_tokens=10,
        )
        label = (resp.choices[0].message.content or "").strip().lower()
        # Normalize common variants
        norm = {
            "payments": "payments_billing",
            "billing": "payments_billing",
            "payment": "payments_billing",
            "returns": "returns_exchanges",
            "exchanges": "returns_exchanges",
            "shipping": "shipping_delivery",
            "delivery": "shipping_delivery",
            "order": "order_management",
            "account": "customer_account",
            "product": "product_information",
        }
        label = norm.get(label, label)
        allowed = {
            "payments_billing",
            "returns_exchanges",
            "shipping_delivery",
            "order_management",
            "customer_account",
            "product_information",
            "chitchat",
        }
        return label if label in allowed else None
    except Exception:
        return None


def _classify_intent_fallback(query: str) -> IntentType:
    q = (query or "").strip().lower()
    if any(k in q for k in ["hi", "hello", "hey", "thank you", "thanks", "how are you"]):
        return "chitchat"
    if any(k in q for k in ["refund", "return", "exchange"]):
        return "returns_exchanges"
    if any(k in q for k in ["ship", "delivery", "deliver", "tracking", "track"]):
        return "shipping_delivery"
    if any(k in q for k in ["order", "cancel", "modify", "change order"]):
        return "order_management"
    if any(k in q for k in ["account", "password", "login", "profile", "address"]):
        return "customer_account"
    if any(k in q for k in ["payment", "billing", "invoice", "charge"]):
        return "payments_billing"
    if any(k in q for k in ["product", "spec", "availability", "detail"]):
        return "product_information"
    return "product_information"


def classify_intent(query: str) -> IntentType:
    label = _classify_intent_llm(query)
    if label is not None:
        return label  # type: ignore[return-value]
    return _classify_intent_fallback(query)


def predict_intent_debug(query: str) -> dict:
    label = _classify_intent_llm(query)
    if label is not None:
        return {"source": "llm", "intent": label}
    fb = _classify_intent_fallback(query)
    return {"source": "fallback", "intent": fb}


def decide_should_retrieve(query: str, intent: str) -> bool:
    return intent != "chitchat"


def router_node(state: RAGState) -> RAGState:
    intent = classify_intent(state.query)
    state.intent = intent
    state.should_retrieve = decide_should_retrieve(state.query, intent)
    return state


