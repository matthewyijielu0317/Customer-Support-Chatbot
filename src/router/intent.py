from typing import Literal


Intent = Literal["policy_qna", "customer_order", "product_info", "chitchat"]


def classify_intent(query: str) -> Intent:
    """Very simple placeholder router. Replace with LLM or rules later."""
    q = query.lower()
    if any(k in q for k in ["order", "tracking", "refund", "return", "exchange"]):
        return "customer_order"
    if any(k in q for k in ["size", "spec", "compatibility", "sku"]):
        return "product_info"
    if any(k in q for k in ["policy", "shipping", "delivery", "billing", "account"]):
        return "policy_qna"
    return "chitchat"


