from __future__ import annotations

from unittest.mock import patch

from src.graph.nodes.retrieve_sql import retrieve_sql_node
from src.graph.state import RAGState


def make_state(query: str, user_id: str | None = "user@example.com") -> RAGState:
    return RAGState(
        query=query,
        user_id=user_id,
        session_id="sess",
        should_retrieve_sql=True,
    )


@patch("src.graph.nodes.retrieve_sql._ENGINE", new=object())
def test_retrieve_sql_requires_user_id():
    state = make_state("order #123", user_id=None)
    state.order_id = 123
    new_state = retrieve_sql_node(state)
    assert new_state.sql_rows == []
    assert new_state.order_id == 123


@patch("src.graph.nodes.retrieve_sql._ENGINE", new=object())
@patch("src.graph.nodes.retrieve_sql.q")
def test_order_lookup_scoped_to_user(mock_queries):
    mock_queries.get_order_for_user.return_value = {
        "order_id": 1,
        "customer_email": "user@example.com",
        "first_name": "Alice",
        "last_name": "Doe",
    }

    state = make_state("order #1")
    result = retrieve_sql_node(state)

    mock_queries.get_order_for_user.assert_called_once()
    assert mock_queries.get_order_for_user.call_args[0][1] == state.user_id
    assert mock_queries.get_order_for_user.call_args[0][2] == 1

    assert result.sql_rows[0]["order_id"] == 1
    assert result.sql_rows[0]["customer_email"].startswith("u***@")
    assert result.first_name == "Alice"
    assert result.last_name == "Doe"
    assert result.order_id == 1


@patch("src.graph.nodes.retrieve_sql._ENGINE", new=object())
@patch("src.graph.nodes.retrieve_sql.q")
def test_no_order_id_skips_lookup(mock_queries):
    state = make_state("where is my order?")
    result = retrieve_sql_node(state)

    mock_queries.get_order_for_user.assert_not_called()
    assert result.sql_rows == []
    assert result.order_id is None
