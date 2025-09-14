import re
from typing import Dict

from src.graph.state import RAGState


ORDER_RE = re.compile(r"\b(order|#)?(\d{5,})\b")


def query_processor_node(state: RAGState) -> RAGState:
    entities: Dict[str, str] = {}
    m = ORDER_RE.search(state.query)
    if m:
        entities["order_id"] = m.group(2)
    state.entities.update(entities)
    return state


