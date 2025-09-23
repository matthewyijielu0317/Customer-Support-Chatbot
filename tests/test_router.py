from __future__ import annotations

import types

from src.graph.nodes import router as router_module
from src.graph.state import RAGState


def test_router_promotes_numeric_order(monkeypatch):
    monkeypatch.setattr(router_module.settings, "postgres_dsn", "postgresql://example")
    state = RAGState(
        query="18",
        user_id="user@example.com",
        session_id="sess",
        recent_messages=[{"role": "assistant", "content": "Please share the order number."}],
    )

    updated = router_module.router_node(state)

    assert updated.query_type == "order_lookup"
    assert updated.should_retrieve_sql is True
    assert updated.order_id == 18
