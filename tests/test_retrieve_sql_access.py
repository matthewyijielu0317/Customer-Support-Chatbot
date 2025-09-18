from __future__ import annotations

from unittest.mock import patch

from src.graph.nodes.retrieve_sql import retrieve_sql_node
from src.graph.state import RAGState


def make_state(query: str, user_id: str | None = "user@example.com") -> RAGState:
    return RAGState(
        query=query,
        user_id=user_id,
        session_id="sess",
    )


@patch("src.graph.nodes.retrieve_sql._ENGINE", new=object())
def test_retrieve_sql_requires_user_id():
    state = make_state("order #123", user_id=None)
    new_state = retrieve_sql_node(state)
    assert new_state.sql_rows == []


@patch("src.graph.nodes.retrieve_sql._ENGINE", new=object())
@patch("src.graph.nodes.retrieve_sql.q")
def test_order_lookup_scoped_to_user(mock_queries):
    mock_queries.get_order_details_for_user.return_value = {
        "order_id": 1,
        "customer_email": "user@example.com",
    }

    state = make_state("order #1")
    result = retrieve_sql_node(state)

    mock_queries.get_order_details_for_user.assert_called_once()
    assert mock_queries.get_order_details_for_user.call_args[0][1] == state.user_id
    assert mock_queries.get_order_details_for_user.call_args[0][2] == 1

    assert result.sql_rows[0]["order_id"] == 1
    assert result.sql_rows[0]["customer_email"].startswith("u***@")


@patch("src.graph.nodes.retrieve_sql._ENGINE", new=object())
@patch("src.graph.nodes.retrieve_sql.q")
def test_email_lookup_requires_matching_user(mock_queries):
    mock_queries.get_recent_orders_for_user.return_value = [
        {"order_id": 5, "customer_email": "user@example.com"}
    ]
    mock_queries.get_customer_profile.return_value = {
        "customer_id": 7,
        "email": "user@example.com",
    }

    state = make_state("my email user@example.com")
    result = retrieve_sql_node(state)

    mock_queries.get_recent_orders_for_user.assert_called_once()
    assert any(row.get("customer_id") == 7 for row in result.sql_rows)


@patch("src.graph.nodes.retrieve_sql._ENGINE", new=object())
@patch("src.graph.nodes.retrieve_sql.q")
def test_email_lookup_denied_for_other_account(mock_queries):
    state = make_state("order for other@example.com")
    result = retrieve_sql_node(state)
    mock_queries.get_recent_orders_for_user.assert_not_called()
    assert result.sql_rows == []
