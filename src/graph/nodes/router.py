from __future__ import annotations

import re
from typing import Literal

from src.config.settings import settings
from src.graph.state import RAGState
from src.graph.nodes.retrieve_sql import _extract_entities
from src.utils.openai_client import get_openai_client


QueryType = Literal[
    "chitchat",
    "policy_only",
    "needs_identifier",
    "order_lookup",
    "billing_issue",
    "escalation",
]

_POLICY_SUMMARY = (
    "Policies available for reference: Customer_Account_Management_Policy.pdf (account access and profile updates), "
    "Returns_and_Exchanges_Policy.pdf (return windows and processes), Shipping_and_Delivery_Policy.pdf (shipping methods and delays), "
    "Order_Management_Guide.pdf (order status, cancellations), Payment_and_Billing_Policy.pdf (charges, refunds, invoices), "
    "Product_Information_Guide.pdf (product specs and availability)."
)


def _classify_query_type_llm(query: str) -> str | None:
    labels = "chitchat | policy_only | needs_identifier | order_lookup | billing_issue | escalation"
    system = (
        "You classify customer support queries for an e-commerce assistant into one label. "
        "Choose exactly one of the allowed labels and answer with ONLY that label.\n\n"
        "Label guide:\n"
        "- chitchat: greetings or small talk.\n"
        "- policy_only: general questions about returns, shipping, accounts, or products with no specific order/account identifiers.\n"
        "- needs_identifier: user is asking about an order but has not provided an order number yet.\n"
        "- order_lookup: user supplied an order number and wants order status/details.\n"
        "- billing_issue: double charges, refunds, or payment problems that typically require transaction lookups plus policy context.\n"
        "- escalation: explicit request for a human agent, supervisor, or complaint escalation.\n\n"
        f"{_POLICY_SUMMARY}"
    )
    user = (
        f"Valid labels: {labels}.\n"
        f"User query: {query}\n"
        "Respond with the single best label only."
    )
    client = get_openai_client()
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            max_tokens=10,
        )
        label = (resp.choices[0].message.content or "").strip().lower()
        allowed = {
            "chitchat",
            "policy_only",
            "needs_identifier",
            "order_lookup",
            "billing_issue",
            "escalation",
        }
        return label if label in allowed else None
    except Exception:
        return None


def _classify_query_type_fallback(query: str) -> QueryType:
    q = (query or "").strip().lower()
    if any(k in q for k in ["hi", "hello", "hey", "thank you", "thanks", "how are you"]):
        return "chitchat"
    if any(k in q for k in ["agent", "representative", "escalate", "supervisor", "complaint"]):
        return "escalation"
    if any(k in q for k in ["refund", "charge", "billing", "payment", "invoice", "credit card", "double charge"]):
        return "billing_issue"
    if any(k in q for k in ["order", "tracking", "track", "shipment", "delivery", "package"]):
        return "order_lookup"
    if any(k in q for k in ["account", "password", "login", "profile", "address"]):
        return "policy_only"
    if any(k in q for k in ["return", "exchange", "shipping", "policy", "product", "spec", "availability"]):
        return "policy_only"
    return "policy_only"


def classify_query_type(query: str) -> QueryType:
    label = _classify_query_type_llm(query)
    if label is not None:
        return label  # type: ignore[return-value]
    return _classify_query_type_fallback(query)


def predict_query_type_debug(query: str) -> dict:
    label = _classify_query_type_llm(query)
    if label is not None:
        return {"source": "llm", "query_type": label}
    fb = _classify_query_type_fallback(query)
    return {"source": "fallback", "query_type": fb}


def router_node(state: RAGState) -> RAGState:
    query = state.query
    state.should_retrieve_sql = False
    state.should_retrieve_docs = False
    state.should_escalate = False

    entities = _extract_entities(query)
    order_id = entities.get("order_id")
    if order_id is not None:
        try:
            state.order_id = int(order_id)
        except (TypeError, ValueError):
            state.order_id = None
    has_identifier = bool(state.order_id)

    query_type = classify_query_type(query)

    if has_identifier:
        query_type = "order_lookup"

    if query_type == "order_lookup" and not has_identifier:
        query_type = "needs_identifier"
    if query_type in {"order_lookup", "billing_issue"} and not settings.postgres_dsn:
        query_type = "policy_only" if query_type == "billing_issue" else "needs_identifier"

    state.query_type = query_type

    q_lower = (query or "").strip().lower()

    if query_type == "chitchat":
        return state

    if query_type == "escalation":
        state.should_escalate = True
        return state

    if query_type == "policy_only":
        state.should_retrieve_docs = True
        return state

    if query_type == "needs_identifier":
        return state

    if query_type == "order_lookup":
        if has_identifier and settings.postgres_dsn:
            state.should_retrieve_sql = True
            if any(k in q_lower for k in ["refund", "policy", "return", "late", "delay", "delivery"]):
                state.should_retrieve_docs = True
        return state

    if query_type == "billing_issue":
        state.should_retrieve_docs = True
        if settings.postgres_dsn and has_identifier:
            state.should_retrieve_sql = True
        return state

    state.should_retrieve_docs = True
    return state
